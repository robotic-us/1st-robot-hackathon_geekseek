import asyncio
import os
import unittest
from unittest.mock import patch

from geekseek.robot import FakeRobot, RvizRobot, pose_for_template


class FakeProcess:
    def __init__(self, returncode=0, stderr=b"") -> None:
        self.returncode = returncode
        self.stderr = stderr
        self.terminated = False

    async def communicate(self):
        await asyncio.sleep(0)
        return b"", self.stderr

    async def wait(self):
        return self.returncode

    def terminate(self):
        self.terminated = True
        self.returncode = -15

    def kill(self):
        self.returncode = -9


class RobotTests(unittest.IsolatedAsyncioTestCase):
    async def test_fake_robot_records_semantic_pose(self) -> None:
        robot = FakeRobot(0)
        await robot.move_to(pose_for_template("upper_body"))
        self.assertEqual(robot.moves, ["frame.upper_body"])

    async def test_rviz_robot_waits_for_status_and_publish_processes(self) -> None:
        status = FakeProcess()
        publisher = FakeProcess()
        calls = []

        async def create_process(*arguments, **kwargs):
            calls.append((arguments, kwargs))
            return status if len(calls) == 1 else publisher

        with patch("asyncio.create_subprocess_exec", side_effect=create_process):
            robot = RvizRobot(move_seconds=0)
            await robot.move_to("frame.full_body")

        self.assertEqual(robot.moves, ["frame.full_body"])
        self.assertTrue(any("completed:frame.full_body" in value for value in calls[0][0]))
        self.assertIn("frame.full_body", calls[1][0][-1])
        self.assertTrue(calls[0][1]["env"]["PYTHONPATH"].startswith("/opt/ros/humble"))

    def test_ros_environment_preserves_existing_pythonpath(self) -> None:
        with patch.dict(os.environ, {"PYTHONPATH": "/workspace/src"}):
            environment = RvizRobot._ros_environment()
        self.assertTrue(environment["PYTHONPATH"].endswith("/workspace/src"))
