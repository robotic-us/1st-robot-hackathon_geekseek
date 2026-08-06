from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class CaptureResult:
    photo_url: str


class CaptureDevice(Protocol):
    async def capture(self) -> CaptureResult: ...


class FakeCapture:
    def __init__(self, capture_seconds: float = 0.2) -> None:
        self.capture_seconds = capture_seconds
        self.count = 0

    async def capture(self) -> CaptureResult:
        await asyncio.sleep(self.capture_seconds)
        self.count += 1
        return CaptureResult(photo_url=f"/api/fake-photo/{self.count}.svg")
