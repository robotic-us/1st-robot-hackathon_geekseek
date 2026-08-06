from __future__ import annotations

import threading
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
        self._connections = vision.PoseLandmarksConnections().POSE_LANDMARKS
        self._last_landmarks: list | None = None

    def sense(self, frame: object) -> PersonSignal:
        rgb = frame[:, :, ::-1]  # cv2 gives BGR; mediapipe wants RGB
        mp_image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb)
        result = self._landmarker.detect(mp_image)
        if not result.pose_landmarks:
            self._last_landmarks = None
            return PersonSignal(detected=False)

        # Low-confidence poses can place unseen joints anywhere, including
        # far outside the frame (x/y outside [0, 1]) — drop those landmarks
        # and require enough confidently-visible ones left to trust the box.
        landmarks = result.pose_landmarks[0]
        self._last_landmarks = landmarks
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

    def annotate_jpeg(self, frame: object, signal: PersonSignal, approaching: bool, positioned: bool) -> bytes:
        """Draws the skeleton (from the most recent sense() call) plus a status
        readout onto a copy of frame, for a live debug view — never called from
        the hot sense() path, only by the coordinator's debug stream."""
        import cv2

        annotated = frame.copy()
        height, width = annotated.shape[:2]
        if self._last_landmarks is not None:
            points = [
                (int(p.x * width), int(p.y * height))
                if p.visibility >= self._min_landmark_visibility
                else None
                for p in self._last_landmarks
            ]
            for connection in self._connections:
                start, end = points[connection.start], points[connection.end]
                if start is not None and end is not None:
                    cv2.line(annotated, start, end, (80, 220, 120), 2)
            for point in points:
                if point is not None:
                    cv2.circle(annotated, point, 4, (60, 140, 255), -1)

        lines = [
            f"detected={signal.detected}  size_ratio={signal.size_ratio:.3f}",
            f"center=({signal.center_x:.2f}, {signal.center_y:.2f})",
            f"approaching={approaching}  positioned={positioned}",
        ]
        for index, line in enumerate(lines):
            y = 28 + index * 26
            cv2.putText(annotated, line, (12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 4)
            color = (120, 255, 120) if index == 2 and (approaching or positioned) else (255, 255, 255)
            cv2.putText(annotated, line, (12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1)

        ok, buffer = cv2.imencode(".jpg", annotated)
        return buffer.tobytes() if ok else b""

    def mirror_jpeg(self, frame: object) -> bytes:
        """Selfie-mirrored, overlay-free JPEG for the guest-facing live camera
        preview (iPad2) — cheap (flip + encode only), safe to compute every
        sense-loop tick alongside the debug overlay."""
        import cv2

        mirrored = cv2.flip(frame, 1)
        ok, buffer = cv2.imencode(".jpg", mirrored)
        return buffer.tobytes() if ok else b""

    def close(self) -> None:
        self._landmarker.close()


class WebcamFrameSource:
    """Grabs frames from a cv2 webcam on a background thread so the async
    sense loop (Coordinator) never blocks the event loop on cv2's blocking
    capture.read(). Call the instance to get the most recent frame (or None
    before the first frame arrives)."""

    def __init__(self, camera_index: int = 0) -> None:
        import cv2

        self._capture = cv2.VideoCapture(camera_index)
        if not self._capture.isOpened():
            raise RuntimeError(f"could not open camera index {camera_index}")
        self._latest: object | None = None
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self) -> None:
        while self._running:
            ok, frame = self._capture.read()
            if ok:
                self._latest = frame

    def __call__(self) -> object | None:
        return self._latest

    def close(self) -> None:
        self._running = False
        self._thread.join(timeout=1.0)
        self._capture.release()


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
