from __future__ import annotations

import json
import math
import time

import pytest

from geekseek.pose_capture import (
    AxisPose,
    FeedbackSnapshot,
    PoseCaptureError,
    save_pose_sample,
    validate_snapshot,
    wrapped_delta,
)


def snapshot(*, speed_deg_s: float = 0.0) -> FeedbackSnapshot:
    return FeedbackSnapshot(
        captured_at="2026-08-08T12:00:00.000+09:00",
        monotonic_seconds=time.monotonic(),
        axes=tuple(
            AxisPose(
                index=index,
                position_rad=math.radians(index * 10),
                velocity_rad_s=math.radians(speed_deg_s),
                valid=True,
            )
            for index in range(5)
        ),
    )


def test_rejects_moving_robot() -> None:
    with pytest.raises(PoseCaptureError, match="움직이는 중"):
        validate_snapshot(snapshot(speed_deg_s=1.0), max_age_seconds=0.2, max_speed_deg_s=0.5)


def test_saves_paired_image_and_metadata(tmp_path) -> None:
    result = save_pose_sample(tmp_path, b"jpeg-data", snapshot(), snapshot())

    image_path = tmp_path / str(result["image"])
    metadata_path = tmp_path / f"{result['sample_id']}.json"
    assert image_path.read_bytes() == b"jpeg-data"
    saved = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert saved["feedback_at_trigger"]["position_deg"] == [0.0, 10.0, 20.0, 30.0, 40.0]
    assert saved["movement_during_capture_deg"] == [0.0] * 5


def test_applies_wrapped_zero_offsets_to_saved_metadata(tmp_path) -> None:
    current = snapshot()
    offsets = {axis.index: axis.position_rad for axis in current.axes}
    result = save_pose_sample(
        tmp_path,
        b"jpeg-data",
        current,
        current,
        offsets,
        "servo-zero-sample",
    )

    saved = json.loads((tmp_path / f"{result['sample_id']}.json").read_text(encoding="utf-8"))
    assert saved["zero_reference"] == "servo-zero-sample"
    assert saved["feedback_at_trigger"]["zeroed_position_deg"] == [0.0] * 5
    assert math.isclose(wrapped_delta(-math.pi + 0.1, math.pi - 0.1), 0.2)


def test_saves_webcam_and_skeleton_with_same_sample_id(tmp_path) -> None:
    inference = {
        "detected": True,
        "people": 1,
        "delegate": "cpu",
        "frame_age_seconds": 0.03,
    }
    result = save_pose_sample(
        tmp_path,
        b"iphone-jpeg",
        snapshot(),
        snapshot(),
        webcam_image=b"webcam-jpeg",
        webcam_skeleton_image=b"skeleton-jpeg",
        webcam_metadata=inference,
    )

    assert (tmp_path / str(result["webcam_image"])).read_bytes() == b"webcam-jpeg"
    assert (tmp_path / str(result["webcam_skeleton_image"])).read_bytes() == b"skeleton-jpeg"
    saved = json.loads((tmp_path / f"{result['sample_id']}.json").read_text(encoding="utf-8"))
    assert saved["webcam_inference"] == inference
