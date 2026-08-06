from __future__ import annotations

import asyncio
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
    """Thin ROS boundary: publish a semantic pose without importing rclpy."""

    def __init__(self, move_seconds: float = 1.2, ros2: str = "/opt/ros/humble/bin/ros2") -> None:
        super().__init__(move_seconds)
        self.ros2 = ros2

    async def move_to(self, pose: str) -> None:
        self.moves.append(pose)
        payload = f"{{data: '{pose}'}}"
        process = await asyncio.create_subprocess_exec(
            self.ros2,
            "topic",
            "pub",
            "--once",
            "/geekseek/fake_robot/target",
            "std_msgs/msg/String",
            payload,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            _, stderr = await asyncio.wait_for(process.communicate(), timeout=3.0)
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise RuntimeError("RViz fake robot command timed out")
        if process.returncode:
            raise RuntimeError(stderr.decode().strip() or "RViz fake robot command failed")
        await asyncio.sleep(self.move_seconds)


def pose_for_template(template_id: str) -> str:
    return {
        "full_body": "frame.full_body",
        "upper_body": "frame.upper_body",
        "product_closeup": "frame.product_closeup",
    }.get(template_id, "frame.full_body")
