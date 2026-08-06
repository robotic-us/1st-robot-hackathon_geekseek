from __future__ import annotations

import asyncio
import os
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
    """Thin ROS boundary that waits for the simulator's completion feedback."""

    def __init__(self, move_seconds: float = 1.2, ros2: str = "/opt/ros/humble/bin/ros2") -> None:
        super().__init__(move_seconds)
        self.ros2 = ros2

    async def move_to(self, pose: str) -> None:
        self.moves.append(pose)
        environment = self._ros_environment()
        completion = f"completed:{pose}"
        status_process = await asyncio.create_subprocess_exec(
            self.ros2,
            "topic",
            "echo",
            "/geekseek/fake_robot/status",
            "std_msgs/msg/String",
            "--filter",
            f"m.data == '{completion}'",
            "--once",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
            env=environment,
        )

        payload = f"{{data: '{pose}'}}"
        publish_process = await asyncio.create_subprocess_exec(
            self.ros2,
            "topic",
            "pub",
            "--once",
            "/geekseek/fake_robot/target",
            "std_msgs/msg/String",
            payload,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
            env=environment,
        )
        try:
            _, publish_stderr = await asyncio.wait_for(publish_process.communicate(), timeout=3.0)
        except asyncio.TimeoutError:
            await self._terminate(status_process)
            publish_process.kill()
            await publish_process.wait()
            raise RuntimeError("RViz fake robot has no target subscriber")
        if publish_process.returncode:
            await self._terminate(status_process)
            raise RuntimeError(publish_stderr.decode().strip() or "RViz fake robot command failed")

        try:
            _, status_stderr = await asyncio.wait_for(
                status_process.communicate(),
                timeout=max(5.0, self.move_seconds + 3.0),
            )
        except asyncio.TimeoutError:
            await self._terminate(status_process)
            raise RuntimeError(f"RViz fake robot did not complete {pose}")
        if status_process.returncode:
            raise RuntimeError(status_stderr.decode().strip() or "RViz feedback listener failed")

    @staticmethod
    async def _terminate(process: asyncio.subprocess.Process) -> None:
        if process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()

    @staticmethod
    def _ros_environment() -> dict[str, str]:
        environment = os.environ.copy()
        required = [
            "/opt/ros/humble/lib/python3.10/site-packages",
            "/opt/ros/humble/local/lib/python3.10/dist-packages",
        ]
        current = environment.get("PYTHONPATH", "").split(os.pathsep)
        environment["PYTHONPATH"] = os.pathsep.join(required + [item for item in current if item])
        return environment


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
