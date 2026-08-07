from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class RuntimeConfig:
    robot: str = "fake"
    capture: str = "fake"
    move_seconds: float = 0.2
    capture_seconds: float = 0.2
    person_sensor: str = "fake"
    camera_index: int = 0
    camera_fps: float = 15.0
    camera_width: int = 640
    camera_height: int = 480
    sense_interval: float = 0.2
    greeting_seconds: float = 3.0
    preview_seconds: float = 3.0
    farewell_seconds: float = 4.0
    vlm_enabled: bool = False
    debug_window: bool = False


@dataclass(frozen=True)
class WebConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    ssl_keyfile: str | None = None
    ssl_certfile: str | None = None


@dataclass(frozen=True)
class AppConfig:
    runtime: RuntimeConfig = RuntimeConfig()
    web: WebConfig = WebConfig()


def load_config(path: str | Path) -> AppConfig:
    raw: dict[str, Any] = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return AppConfig(
        runtime=RuntimeConfig(**raw.get("runtime", {})),
        web=WebConfig(**raw.get("web", {})),
    )
