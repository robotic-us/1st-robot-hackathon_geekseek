from __future__ import annotations

import asyncio
import sys
import threading
from typing import Protocol


class Robot(Protocol):
    async def move_to(self, pose: str) -> None: ...


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
