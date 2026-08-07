from __future__ import annotations

import json
import math
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class AxisPose:
    index: int
    position_rad: float
    velocity_rad_s: float
    valid: bool
    pos_ref_echo_rad: float | None = None


@dataclass(frozen=True)
class FeedbackSnapshot:
    captured_at: str
    monotonic_seconds: float
    axes: tuple[AxisPose, ...]


class FeedbackStore:
    """Thread-safe handoff from the rclpy feedback thread to FastAPI."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._latest: FeedbackSnapshot | None = None

    def update(self, snapshot: FeedbackSnapshot) -> None:
        with self._lock:
            self._latest = snapshot

    def latest(self) -> FeedbackSnapshot | None:
        with self._lock:
            return self._latest


class PoseCaptureError(RuntimeError):
    pass


def validate_snapshot(
    snapshot: FeedbackSnapshot | None,
    *,
    max_age_seconds: float,
    max_speed_deg_s: float,
) -> FeedbackSnapshot:
    if snapshot is None:
        raise PoseCaptureError("아직 /phorce/feedback 데이터가 없습니다")

    age = time.monotonic() - snapshot.monotonic_seconds
    if age > max_age_seconds:
        raise PoseCaptureError(f"로봇 피드백이 오래되었습니다 ({age:.2f}초)")

    invalid = [axis.index for axis in snapshot.axes if not axis.valid]
    if invalid:
        raise PoseCaptureError(f"valid가 아닌 축이 있습니다: {invalid}")

    fastest = max((abs(math.degrees(axis.velocity_rad_s)) for axis in snapshot.axes), default=0.0)
    if fastest > max_speed_deg_s:
        raise PoseCaptureError(
            f"로봇팔이 아직 움직이는 중입니다 (최대 {fastest:.2f} deg/s, "
            f"허용 {max_speed_deg_s:.2f} deg/s)"
        )
    return snapshot


def wrapped_delta(current_rad: float, zero_rad: float) -> float:
    return math.atan2(math.sin(current_rad - zero_rad), math.cos(current_rad - zero_rad))


def snapshot_dict(
    snapshot: FeedbackSnapshot,
    zero_offsets_rad: dict[int, float] | None = None,
) -> dict[str, object]:
    data: dict[str, object] = {
        "captured_at": snapshot.captured_at,
        "axis_indices": [axis.index for axis in snapshot.axes],
        "position_rad": [round(axis.position_rad, 9) for axis in snapshot.axes],
        "position_deg": [round(math.degrees(axis.position_rad), 6) for axis in snapshot.axes],
        "velocity_rad_s": [round(axis.velocity_rad_s, 9) for axis in snapshot.axes],
        "velocity_deg_s": [round(math.degrees(axis.velocity_rad_s), 6) for axis in snapshot.axes],
        "pos_ref_echo_rad": [
            None if axis.pos_ref_echo_rad is None else round(axis.pos_ref_echo_rad, 9)
            for axis in snapshot.axes
        ],
        "valid": [axis.valid for axis in snapshot.axes],
    }
    if zero_offsets_rad is not None:
        offsets = [zero_offsets_rad[axis.index] for axis in snapshot.axes]
        zeroed = [wrapped_delta(axis.position_rad, zero_offsets_rad[axis.index]) for axis in snapshot.axes]
        data.update(
            {
                "zero_offset_rad": [round(value, 9) for value in offsets],
                "zero_offset_deg": [round(math.degrees(value), 6) for value in offsets],
                "zeroed_position_rad": [round(value, 9) for value in zeroed],
                "zeroed_position_deg": [round(math.degrees(value), 6) for value in zeroed],
            }
        )
    return data


def save_pose_sample(
    save_dir: Path,
    image: bytes,
    trigger: FeedbackSnapshot,
    received: FeedbackSnapshot,
    zero_offsets_rad: dict[int, float] | None = None,
    zero_reference: str | None = None,
    webcam_image: bytes | None = None,
    webcam_skeleton_image: bytes | None = None,
    webcam_metadata: dict[str, object] | None = None,
) -> dict[str, object]:
    if not image:
        raise PoseCaptureError("휴대폰에서 빈 이미지가 도착했습니다")

    timestamp = datetime.now().astimezone()
    stem = timestamp.strftime("pose_%Y%m%d_%H%M%S_%f")
    image_name = f"{stem}.jpg"
    webcam_image_name = f"{stem}_webcam.jpg" if webcam_image is not None else None
    webcam_skeleton_name = (
        f"{stem}_skeleton.jpg" if webcam_skeleton_image is not None else None
    )
    metadata_name = f"{stem}.json"

    trigger_positions = {axis.index: axis.position_rad for axis in trigger.axes}
    movement_deg = [
        round(math.degrees(axis.position_rad - trigger_positions[axis.index]), 6)
        for axis in received.axes
        if axis.index in trigger_positions
    ]

    metadata: dict[str, object] = {
        "sample_id": stem,
        "saved_at": timestamp.isoformat(timespec="milliseconds"),
        "image": image_name,
        "webcam_image": webcam_image_name,
        "webcam_skeleton_image": webcam_skeleton_name,
        "webcam_inference": webcam_metadata,
        "zero_reference": zero_reference,
        "feedback_at_trigger": snapshot_dict(trigger, zero_offsets_rad),
        "feedback_at_image_receive": snapshot_dict(received, zero_offsets_rad),
        "movement_during_capture_deg": movement_deg,
    }

    save_dir.mkdir(parents=True, exist_ok=True)
    (save_dir / image_name).write_bytes(image)
    if webcam_image_name is not None:
        if not webcam_image:
            raise PoseCaptureError("웹캠 원본 이미지가 비어 있습니다")
        (save_dir / webcam_image_name).write_bytes(webcam_image)
    if webcam_skeleton_name is not None:
        if not webcam_skeleton_image:
            raise PoseCaptureError("웹캠 skeleton 이미지가 비어 있습니다")
        (save_dir / webcam_skeleton_name).write_bytes(webcam_skeleton_image)
    (save_dir / metadata_name).write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return metadata
