from __future__ import annotations

from pathlib import Path

from .capture import FakeCapture, WebAppCapture
from .config import AppConfig
from .coordinator import Coordinator
from .robot import FakeRobot, RvizRobot
from .verification import LocalVerifier

PHOTOS_DIR = Path(__file__).resolve().parents[2] / "photos"


def build_coordinator(config: AppConfig) -> Coordinator:
    robot = (
        RvizRobot(config.runtime.move_seconds)
        if config.runtime.robot == "rviz"
        else FakeRobot(config.runtime.move_seconds)
    )
    capture = (
        WebAppCapture(PHOTOS_DIR)
        if config.runtime.capture == "webapp"
        else FakeCapture(config.runtime.capture_seconds)
    )
    verifier = LocalVerifier()
    return Coordinator(robot=robot, capture=capture, verifier=verifier)
