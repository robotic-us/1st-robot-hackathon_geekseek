from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "pose_landmarker_lite.task"


@dataclass(frozen=True)
class PersonSignal:
    detected: bool
    size_ratio: float = 0.0  # visible-landmark bbox area / frame area, 0..1
    center_x: float = 0.5  # normalized 0..1, bbox center
    center_y: float = 0.5


class PersonSensor(Protocol):
    def sense(self, frame: object) -> PersonSignal: ...


class FakePersonSensor:
    """Returns a scripted sequence of signals, one per sense() call (repeats the last)."""

    def __init__(self, signals: list[PersonSignal] | None = None) -> None:
        self.signals = signals or [PersonSignal(detected=False)]
        self._index = 0

    def sense(self, frame: object) -> PersonSignal:
        signal = self.signals[min(self._index, len(self.signals) - 1)]
        self._index += 1
        return signal


class MediaPipePersonSensor:
    """Wraps MediaPipe's PoseLandmarker (IMAGE mode) to derive a coarse
    "how close / how centered" signal from a single BGR frame (e.g. from
    cv2.VideoCapture) — enough for the scenario's 2단계(접근 감지)와
    4→5단계(정위치 확인). Full landmark keypoints stay on the raw result if a
    later feature (AR 가이드 등) needs them; this class only exposes the
    reduced signal."""

    def __init__(
        self,
        model_path: Path = MODEL_PATH,
        min_detection_confidence: float = 0.5,
        min_landmark_visibility: float = 0.5,
        min_visible_landmarks: int = 8,
    ) -> None:
        import mediapipe as mp
        from mediapipe.tasks.python import BaseOptions
        from mediapipe.tasks.python import vision

        options = vision.PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.IMAGE,
            num_poses=1,
            min_pose_detection_confidence=min_detection_confidence,
        )
        self._mp = mp
        self._landmarker = vision.PoseLandmarker.create_from_options(options)
        self._min_landmark_visibility = min_landmark_visibility
        self._min_visible_landmarks = min_visible_landmarks

    def sense(self, frame: object) -> PersonSignal:
        rgb = frame[:, :, ::-1]  # cv2 gives BGR; mediapipe wants RGB
        mp_image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb)
        result = self._landmarker.detect(mp_image)
        if not result.pose_landmarks:
            return PersonSignal(detected=False)

        # Low-confidence poses can place unseen joints anywhere, including
        # far outside the frame (x/y outside [0, 1]) — drop those landmarks
        # and require enough confidently-visible ones left to trust the box.
        landmarks = result.pose_landmarks[0]
        visible = [point for point in landmarks if point.visibility >= self._min_landmark_visibility]
        if len(visible) < self._min_visible_landmarks:
            return PersonSignal(detected=False)

        xs = [min(1.0, max(0.0, point.x)) for point in visible]
        ys = [min(1.0, max(0.0, point.y)) for point in visible]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        return PersonSignal(
            detected=True,
            size_ratio=max(0.0, max_x - min_x) * max(0.0, max_y - min_y),
            center_x=(min_x + max_x) / 2,
            center_y=(min_y + max_y) / 2,
        )

    def close(self) -> None:
        self._landmarker.close()


def is_approaching(signal: PersonSignal, size_threshold: float = 0.12) -> bool:
    """시나리오 2단계: skeleton이 일정 크기 이상이면 접근으로 판단."""
    return signal.detected and signal.size_ratio >= size_threshold


def is_positioned(
    signal: PersonSignal,
    center_x_range: tuple[float, float] = (0.35, 0.65),
    center_y_range: tuple[float, float] = (0.3, 0.85),
) -> bool:
    """시나리오 4→5단계: 표시된 위치(화면 중앙 하단 영역)로 이동했는지 판단."""
    if not signal.detected:
        return False
    return center_x_range[0] <= signal.center_x <= center_x_range[1] and (
        center_y_range[0] <= signal.center_y <= center_y_range[1]
    )
