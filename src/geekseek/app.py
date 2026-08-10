from __future__ import annotations

import logging
from pathlib import Path

from .capture import FakeCapture, WebAppCapture
from .config import AppConfig
from .coordinator import Coordinator
from .framing_guide import load_templates_from_dataset
from .gallery import Gallery
from .perception import FakePersonSensor, MediaPipePersonSensor, WebcamFrameSource
from .robot import FakeRobot, PhorceRobot, RvizRobot
from .vlm import ClaudeGreeter

PHOTOS_DIR = Path(__file__).resolve().parents[2] / "photos"


REPO_ROOT = Path(__file__).resolve().parents[2]
LOGGER = logging.getLogger(__name__)


def build_robot(config: AppConfig):
    if config.runtime.robot == "phorce":
        return PhorceRobot(
            motion_ids=config.runtime.phorce_motion_ids,
            slot_dir=REPO_ROOT / config.runtime.phorce_slot_dir,
            timeout_seconds=config.runtime.phorce_timeout_seconds,
            busy_retries=config.runtime.phorce_busy_retries,
            busy_retry_seconds=config.runtime.phorce_busy_retry_seconds,
        )
    if config.runtime.robot == "rviz":
        return RvizRobot(config.runtime.move_seconds)
    return FakeRobot(config.runtime.move_seconds)


def build_gallery(config: AppConfig) -> Gallery:
    return Gallery(base_url=config.runtime.gallery_base_url)


def build_coordinator(config: AppConfig, gallery: Gallery | None = None) -> Coordinator:
    robot = build_robot(config)
    capture = (
        WebAppCapture(PHOTOS_DIR)
        if config.runtime.capture == "webapp"
        else FakeCapture(config.runtime.capture_seconds)
    )

    person_sensor = None
    frame_source = None
    framing_templates = {}
    live_frame_interval = 1 / config.runtime.camera_fps
    if config.runtime.person_sensor == "mediapipe":
        person_sensor = MediaPipePersonSensor()
        dataset_dir = REPO_ROOT / config.runtime.framing_dataset_dir
        try:
            framing_templates = load_templates_from_dataset(person_sensor, dataset_dir)
            LOGGER.info(
                "framing templates loaded: %s",
                {mode: template.sample_count for mode, template in framing_templates.items()},
            )
        except (FileNotFoundError, ValueError) as exc:
            LOGGER.warning("framing templates unavailable; using center-only guide: %s", exc)
        frame_source = WebcamFrameSource(
            config.runtime.camera_index,
            config.runtime.camera_fps,
            config.runtime.camera_width,
            config.runtime.camera_height,
            config.runtime.camera_fourcc,
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
        slide_seconds=config.runtime.slide_seconds,
        gallery=gallery if gallery is not None else build_gallery(config),
        photo_target_count=config.runtime.photo_target_count,
        framing_templates=framing_templates,
    )
