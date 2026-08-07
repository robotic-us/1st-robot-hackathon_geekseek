from __future__ import annotations

from pathlib import Path

from .capture import FakeCapture, WebAppCapture
from .config import AppConfig
from .coordinator import Coordinator
from .perception import FakePersonSensor, MediaPipePersonSensor, WebcamFrameSource
from .robot import FakeRobot, RvizRobot
from .vlm import ClaudeGreeter

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

    person_sensor = None
    frame_source = None
    live_frame_interval = 1 / config.runtime.camera_fps
    if config.runtime.person_sensor == "mediapipe":
        person_sensor = MediaPipePersonSensor()
        frame_source = WebcamFrameSource(
            config.runtime.camera_index,
            config.runtime.camera_fps,
            config.runtime.camera_width,
            config.runtime.camera_height,
        )
    elif config.runtime.person_sensor == "fake":
        person_sensor = FakePersonSensor()

    greeter = ClaudeGreeter() if config.runtime.vlm_enabled else None

    return Coordinator(
        robot=robot,
        capture=capture,
        person_sensor=person_sensor,
        frame_source=frame_source,
        greeter=greeter,
        sense_interval=config.runtime.sense_interval,
        live_frame_interval=live_frame_interval,
        greeting_seconds=config.runtime.greeting_seconds,
        preview_seconds=config.runtime.preview_seconds,
        farewell_seconds=config.runtime.farewell_seconds,
    )
