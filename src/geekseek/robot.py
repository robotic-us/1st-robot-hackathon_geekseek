from __future__ import annotations

import asyncio
import sys
import threading
import time
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Protocol

from .motion_plan import ShotCue, SweepPlan, load_sweep_plan, plan_shot_times

ShotCallback = Callable[[ShotCue], Awaitable[None]]


class Robot(Protocol):
    async def move_to(self, pose: str) -> None: ...


class SweepingRobot(Robot, Protocol):
    """A robot that can play one long motion while the shutter fires on a
    schedule, instead of the move-then-shoot-once loop."""

    async def sweep(self, pose: str, shoot: ShotCallback, target_count: int = 40) -> None: ...


class FakeRobot:
    def __init__(self, move_seconds: float = 0.2) -> None:
        self.move_seconds = move_seconds
        self.moves: list[str] = []

    async def move_to(self, pose: str) -> None:
        self.moves.append(pose)
        await asyncio.sleep(self.move_seconds)


class RvizRobot(FakeRobot):
    """ROS boundary that keeps a single rclpy node alive for the whole
    session, instead of shelling out to a brand-new `ros2 topic echo`/`pub`
    process on every single move.

    That per-move subprocess approach needed a full DDS discovery handshake
    (a cold-start participant finding the fake_robot_node's publisher/
    subscriber) to finish inside a few seconds, every single time — and
    /geekseek/fake_robot/target|status only carry a couple of messages per
    move, so there's nothing keeping discovery "warm" between calls the way
    a continuous topic like /joint_states does. Measured directly against
    phorce: repeated one-shot `ros2 topic info` queries against that same
    topic failed most of the time even though the node was healthy the whole
    time, which is exactly the "did not complete" failure this class used to
    raise intermittently. A persistent node/publisher/subscription discovers
    the graph exactly once, at startup, and reuses that connection for every
    move — so there is no repeated discovery race left to lose.
    """

    _ROS_SITE_PACKAGES = (
        f"/opt/ros/humble/lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages",
        f"/opt/ros/humble/local/lib/python{sys.version_info.major}.{sys.version_info.minor}/dist-packages",
    )

    def __init__(
        self,
        move_seconds: float = 1.2,
        node_name: str = "geekseek_robot_bridge",
        min_status_timeout: float = 5.0,
    ) -> None:
        super().__init__(move_seconds)
        self.min_status_timeout = min_status_timeout
        self._bootstrap_ros_sys_path()

        import rclpy
        from rclpy.executors import SingleThreadedExecutor
        from std_msgs.msg import String

        self._String = String
        self._rclpy = rclpy
        if not rclpy.ok():
            rclpy.init()
        self._node = rclpy.create_node(node_name)
        self._target_publisher = self._node.create_publisher(String, "/geekseek/fake_robot/target", 10)
        self._status_subscription = self._node.create_subscription(
            String, "/geekseek/fake_robot/status", self._on_status, 10
        )

        self._awaited_pose: str | None = None
        self._completed_event: asyncio.Event | None = None
        self._completed_loop: asyncio.AbstractEventLoop | None = None

        self._executor = SingleThreadedExecutor()
        self._executor.add_node(self._node)
        self._spin_thread = threading.Thread(target=self._executor.spin, daemon=True)
        self._spin_thread.start()
        self._wait_for_discovery()

    def _wait_for_discovery(self, timeout_seconds: float = 5.0, poll_seconds: float = 0.05) -> None:
        """Blocks (briefly, once, at startup — not on the asyncio loop yet)
        until fake_robot_node's target subscriber and status publisher have
        actually been found over DDS. Without this, the very first move_to()
        call publishes/listens before discovery finishes and times out even
        though every later call (once discovery has caught up) works fine —
        this trades that one guaranteed-visible stall for a startup delay
        nobody's watching."""
        import time

        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if (
                self._target_publisher.get_subscription_count() >= 1
                and self._node.count_publishers("/geekseek/fake_robot/status") >= 1
            ):
                return
            time.sleep(poll_seconds)

    @classmethod
    def _bootstrap_ros_sys_path(cls) -> None:
        """Make `import rclpy` work even if the launching shell never
        sourced /opt/ros/humble/setup.bash — mutates this process's own
        sys.path since (unlike the old subprocess approach) there is no
        child process whose env we can patch instead."""
        for path in cls._ROS_SITE_PACKAGES:
            if path not in sys.path:
                sys.path.append(path)

    def _on_status(self, message: object) -> None:
        """Runs on the executor's spin thread, not the asyncio loop — only
        touch thread-safe primitives here."""
        if self._awaited_pose is None or message.data != f"completed:{self._awaited_pose}":  # type: ignore[attr-defined]
            return
        event, loop = self._completed_event, self._completed_loop
        if event is not None and loop is not None:
            loop.call_soon_threadsafe(event.set)

    async def move_to(self, pose: str) -> None:
        self.moves.append(pose)
        self._completed_event = asyncio.Event()
        self._completed_loop = asyncio.get_running_loop()
        self._awaited_pose = pose
        try:
            self._target_publisher.publish(self._String(data=pose))
            try:
                await asyncio.wait_for(
                    self._completed_event.wait(), timeout=max(self.min_status_timeout, self.move_seconds + 3.0)
                )
            except asyncio.TimeoutError:
                raise RuntimeError(f"RViz fake robot did not complete {pose}")
        finally:
            self._awaited_pose = None

    def close(self) -> None:
        self._executor.shutdown()
        self._node.destroy_node()
        if self._rclpy.ok():
            self._rclpy.shutdown()
        self._spin_thread.join(timeout=1.0)


class PhorceRobot:
    """Real arm, driven the only way the hackathon SDK allows: `play(slot)` on
    a motion pre-loaded onto the PCM's SD card.

    There is no way to steer the arm mid-motion and no progress signal worth
    keying off — the action's `pvector_index` is transfer progress, not
    playback progress, and its own docstring says so. What we do have is an
    exact schedule: `scripts/build_motion_slots.py` chose every Ltraj itself, so
    the pause windows are known to the millisecond before playback starts. So
    the sweep fires the shutter off a clock started when the goal is accepted,
    and the arm's guaranteed dead-stop at each waypoint is what keeps those
    shots sharp.
    """

    def __init__(
        self,
        motion_ids: dict[str, int],
        slot_dir: Path,
        timeout_seconds: float = 45.0,
        busy_retries: int = 2,
        busy_retry_seconds: float = 1.0,
        target: str = "robot",
        connect_timeout: float = 10.0,
        idle_timeout_seconds: float = 15.0,
        idle_poll_seconds: float = 0.2,
        accept_grace_seconds: float = 1.5,
        late_shot_tolerance: float = 0.35,
        cooldown_seconds: float = 5.0,
    ) -> None:
        self.motion_ids = motion_ids
        self.slot_dir = Path(slot_dir)
        self.timeout_seconds = timeout_seconds
        self.busy_retries = busy_retries
        self.busy_retry_seconds = busy_retry_seconds
        self.target = target
        self.connect_timeout = connect_timeout
        self.idle_timeout_seconds = idle_timeout_seconds
        self.idle_poll_seconds = idle_poll_seconds
        self.accept_grace_seconds = accept_grace_seconds
        self.late_shot_tolerance = late_shot_tolerance
        self.cooldown_seconds = cooldown_seconds
        self.moves: list[str] = []
        RvizRobot._bootstrap_ros_sys_path()

        import phorce

        self._phorce = phorce
        # Connecting is deferred: phorce.connect() blocks and then raises when
        # the two-terminal stack isn't up yet, and the manual lists "started
        # the stack before powering the robot" as a routine mistake. The kiosk
        # web server has to come up regardless so the operator can see why.
        self._robot: object | None = None
        self._connect_lock = asyncio.Lock()
        self._finished_at: float | None = None

    # ── 연결과 사전 검증 ──

    def _connect_and_verify(self):
        """doctor → list → 슬롯 적재 확인. 전부 동기, to_thread에서 부른다."""
        robot = self._phorce.connect(target=self.target, timeout=self.connect_timeout)
        try:
            report = robot.doctor()
            if report.duplicate_action_server:
                raise RuntimeError(
                    "모션 액션 서버가 둘 이상 떠 있습니다 — 어느 쪽이 명령을 받을지 "
                    f"보장할 수 없습니다: {report.action_server_identities}"
                )
            if not report.ok:
                raise RuntimeError("phorce doctor NOT READY: " + "; ".join(report.issues))

            # 정본은 로봇이 적재한 슬롯이지 Jetson의 파일이 아니다 (매뉴얼 §8).
            loaded = {motion.id for motion in robot.motions.list()}
            required = {int(slot) for slot in self.motion_ids.values()}
            missing = sorted(required - loaded)
            if missing:
                raise RuntimeError(
                    f"로봇에 적재되지 않은 슬롯입니다: {missing} "
                    f"(적재됨: {sorted(loaded)}). SD카드에 쓴 뒤 PCM 전원을 "
                    f"껐다 켜야 반영됩니다"
                )
        except Exception:
            robot.close()
            raise
        return robot

    async def preflight(self) -> None:
        """Connect and run every read-only check before anything can move."""
        async with self._connect_lock:
            if self._robot is None:
                self._robot = await asyncio.to_thread(self._connect_and_verify)

    def slot_for(self, pose: str) -> int:
        if pose not in self.motion_ids:
            raise RuntimeError(f"{pose}에 대응하는 phorce 슬롯이 설정에 없습니다")
        return int(self.motion_ids[pose])

    def sweep_plan(self, pose: str) -> SweepPlan:
        slot = self.slot_for(pose)
        schedule = self.slot_dir / f"motion_{slot:02d}.schedule.json"
        if not schedule.exists():
            raise RuntimeError(
                f"슬롯 {slot}의 스케줄 파일이 없습니다: {schedule}. "
                f"scripts/build_motion_slots.py를 먼저 실행하세요"
            )
        return load_sweep_plan(schedule)

    # ── 재생 ──

    async def move_to(self, pose: str) -> None:
        """Robot protocol: play the pose's slot and wait for it to finish."""
        self.moves.append(pose)
        handle, _ = await self._fire(self.slot_for(pose))
        await self._settle(handle)

    async def sweep(self, pose: str, shoot: ShotCallback, target_count: int = 40) -> None:
        """Play the pose's slot end to end, firing `shoot` on schedule."""
        plan = self.sweep_plan(pose)
        cues = plan_shot_times(plan, target_count=target_count)
        self.moves.append(pose)

        handle, fired_at = await self._fire(plan.slot)

        failures = 0
        for cue in cues:
            delay = cue.at_seconds - (time.monotonic() - fired_at)
            if delay > 0:
                await asyncio.sleep(delay)
            elif cue.waypoint is None and -delay > self.late_shot_tolerance:
                # A slow shutter round trip pushes every later cue into the
                # past. Firing them back to back would burst well past the
                # rate the phone bridge is proven at — and they would land
                # mid-travel anyway, which is not what they were scheduled
                # for. Waypoint shots are never dropped; the arm pauses there
                # long enough that a late one is still the intended framing.
                continue
            try:
                await shoot(cue)
            except Exception:
                # A dropped frame must not abandon the arm mid-sweep — the
                # motion cannot be stopped anyway, so keep the clock running
                # and let the remaining cues fire. A total failure is caught
                # below rather than silently returning an empty burst.
                failures += 1

        await self._settle(handle)
        if failures == len(cues):
            raise RuntimeError(f"{len(cues)}번 촬영을 모두 실패했습니다 — 폰 연결을 확인하세요")

    async def _fire(self, slot: int):
        """Wait for the arm to be genuinely idle, send the goal, and only
        return once the goal is known to have been accepted.

        The naive version — send, then treat "no result yet" as success — is
        wrong in the one case that matters: a rejected goal sets its result
        immediately, so a caller that never distinguishes acceptance from
        "still running" happily runs a whole shot schedule against an arm that
        never moved, and only learns about it when the burst is already over.
        """
        for attempt in range(self.busy_retries + 1):
            await self._wait_until_idle()
            handle = self._robot.play_async(slot)
            fired_at = time.monotonic()
            try:
                await self._confirm_accepted(handle)
            except self._phorce.MotionBusy:
                # Code 5 is the only reject the manual says to retry; 12/13
                # need a person at the robot and never clear on their own.
                if attempt == self.busy_retries:
                    raise
                await asyncio.sleep(self.busy_retry_seconds)
                continue
            return handle, fired_at
        raise RuntimeError("unreachable")

    async def _confirm_accepted(self, handle) -> None:
        """A goal that reaches a terminal state inside the grace window was
        rejected, not completed — no slot is short enough. Re-raising through
        wait() turns it into the specific MotionBusy/MotionRejected the caller
        needs to tell "retry" apart from "fetch a human"."""
        deadline = time.monotonic() + self.accept_grace_seconds
        while time.monotonic() < deadline:
            if handle.done:
                await asyncio.to_thread(handle.wait, 1.0)
                raise RuntimeError("모션이 시작되기도 전에 종료됐습니다")
            await asyncio.sleep(0.02)

    async def _settle(self, handle) -> None:
        """Wait out the motion and insist it really succeeded."""
        try:
            result = await asyncio.to_thread(handle.wait, self.timeout_seconds)
        except TimeoutError:
            handle.cancel()
            raise
        finally:
            self._finished_at = time.monotonic()
        if not result.ok:
            raise RuntimeError(
                f"모션이 정상 완료되지 않았습니다 ({result.status_name}, "
                f"physical_idle={result.physical_idle}, "
                f"recovery_required={result.recovery_required}): {result.detail}"
            )

    async def _wait_until_idle(self) -> None:
        """Gate every launch on a fresh IDLE reading.

        There is no queue: a goal sent while the previous motion is still
        settling is dropped, not deferred. And a stale or contract-inactive
        sample cannot stand in for idle — Status says so explicitly, so the
        freshness fields are checked before the idle ones.
        """
        await self.preflight()

        # 과열 자동 차단이 없다 (매뉴얼 §10) — 연속 재생 사이에 쉬어 준다.
        if self._finished_at is not None:
            rest = self.cooldown_seconds - (time.monotonic() - self._finished_at)
            if rest > 0:
                await asyncio.sleep(rest)

        deadline = time.monotonic() + self.idle_timeout_seconds
        last = "상태 표본 없음"
        while time.monotonic() < deadline:
            try:
                status = await asyncio.to_thread(self._robot.status)
            except self._phorce.PhorceError as exc:
                last = str(exc)
            else:
                if not status.contract_active:
                    last = "CONTRACT_INACTIVE — 게이트웨이가 명령 계약을 열지 않았습니다"
                elif not status.is_fresh:
                    last = f"STALE — 상태가 {status.age_ms}ms 지났습니다"
                elif status.boot_id == 0:
                    last = "UNKNOWN — boot_id가 아직 0입니다"
                elif status.state_name == "IDLE":
                    return
                elif status.recovery_required:
                    raise RuntimeError(
                        "로봇이 RECOVERY_REQUIRED 상태입니다 — 2번 버튼으로 파킹한 뒤 "
                        "영점을 다시 잡아야 합니다 (기다려도 풀리지 않습니다)"
                    )
                else:
                    last = f"{status.state_name} (active_motion_id={status.active_motion_id})"
            await asyncio.sleep(self.idle_poll_seconds)
        raise RuntimeError(
            f"{self.idle_timeout_seconds:.1f}초 안에 로봇이 IDLE이 되지 않았습니다: {last}"
        )

    def close(self) -> None:
        if self._robot is not None:
            self._robot.close()
            self._robot = None


def pose_for_template(template_id: str) -> str:
    return {
        "full_body": "frame.full_body",
        "upper_body": "frame.upper_body",
        "product_closeup": "frame.product_closeup",
    }.get(template_id, "frame.full_body")


def burst_poses_for_template(template_id: str) -> list[str]:
    """5단계: 정위치에서 여러 구도로 팔을 움직이며 촬영. 고른 구도를 먼저 찍고
    나머지 두 구도를 이어서 찍는다."""
    all_poses = ["frame.full_body", "frame.upper_body", "frame.product_closeup"]
    first = pose_for_template(template_id)
    return [first] + [pose for pose in all_poses if pose != first]
