from __future__ import annotations

from .capture import FakeCapture
from .config import AppConfig
from .coordinator import Coordinator
from .robot import FakeRobot, RvizRobot
from .verification import LocalVerifier


def build_coordinator(config: AppConfig) -> Coordinator:
    robot = (
        RvizRobot(config.runtime.move_seconds)
        if config.runtime.robot == "rviz"
        else FakeRobot(config.runtime.move_seconds)
    )
    capture = FakeCapture(config.runtime.capture_seconds)
    verifier = LocalVerifier()
    return Coordinator(robot=robot, capture=capture, verifier=verifier)
