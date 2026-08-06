from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class State(str, Enum):
    BOOTING = "booting"
    WAITING = "waiting"  # 1단계: 사람이 지나다니고 있음
    GREETING = "greeting"  # 2단계: 사람이 가까이 다가옴
    DECIDING = "deciding"  # 3단계: 촬영 여부/구도 결정
    GUIDING = "guiding"  # 4단계: 촬영 시작, 위치로 유도
    CAPTURING = "capturing"  # 5단계: 정위치 도달, 버스트 촬영
    PREVIEWING = "previewing"  # 6단계: 촬영 끝, 슬라이드로 보여줌
    ASKING = "asking"  # 7단계: 마음에 드는지 확인
    FAREWELL = "farewell"  # 8단계: 인사, 자리 뜸
    ERROR = "error"


class EventType(str, Enum):
    SYSTEM_READY = "system_ready"
    PERSON_APPROACHED = "person_approached"
    GREETING_DONE = "greeting_done"
    CAPTURE_STARTED = "capture_started"
    DECLINED = "declined"
    POSITION_REACHED = "position_reached"
    BURST_COMPLETE = "burst_complete"
    CAPTURE_FAILED = "capture_failed"
    PREVIEW_DONE = "preview_done"
    REPLAY_REQUESTED = "replay_requested"
    PHOTO_LIKED = "photo_liked"
    FAREWELL_DONE = "farewell_done"
    RESET_REQUESTED = "reset_requested"


@dataclass(frozen=True)
class Event:
    type: EventType
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowContext:
    state: State = State.BOOTING
    template_id: str | None = None
    photos: list[str] = field(default_factory=list)
    hint: str = ""
    error: str = ""
    revision: int = 0

    def as_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["state"] = self.state.value
        return value


class InvalidTransition(ValueError):
    pass


_TRANSITIONS: dict[tuple[State, EventType], State] = {
    (State.BOOTING, EventType.SYSTEM_READY): State.WAITING,
    (State.WAITING, EventType.PERSON_APPROACHED): State.GREETING,
    (State.GREETING, EventType.GREETING_DONE): State.DECIDING,
    (State.DECIDING, EventType.CAPTURE_STARTED): State.GUIDING,
    (State.DECIDING, EventType.DECLINED): State.WAITING,
    (State.GUIDING, EventType.POSITION_REACHED): State.CAPTURING,
    (State.CAPTURING, EventType.BURST_COMPLETE): State.PREVIEWING,
    (State.CAPTURING, EventType.CAPTURE_FAILED): State.ERROR,
    (State.PREVIEWING, EventType.PREVIEW_DONE): State.ASKING,
    (State.ASKING, EventType.REPLAY_REQUESTED): State.PREVIEWING,
    (State.ASKING, EventType.PHOTO_LIKED): State.FAREWELL,
    (State.FAREWELL, EventType.FAREWELL_DONE): State.WAITING,
    (State.ERROR, EventType.RESET_REQUESTED): State.WAITING,
}


def apply_event(context: WorkflowContext, event: Event) -> None:
    """Apply one valid event. The coordinator is the sole caller in production."""
    try:
        next_state = _TRANSITIONS[(context.state, event.type)]
    except KeyError as exc:
        raise InvalidTransition(f"{event.type.value} is invalid in {context.state.value}") from exc

    if event.type is EventType.CAPTURE_STARTED:
        template_id = str(event.data.get("template_id", "")).strip()
        if not template_id:
            raise InvalidTransition("template_id is required")
        context.template_id = template_id
        context.photos = []
        context.hint = ""
    elif event.type is EventType.BURST_COMPLETE:
        context.photos = list(event.data.get("photos", []))
    elif event.type is EventType.CAPTURE_FAILED:
        context.error = str(event.data.get("reason", "unknown error"))
    elif event.type in (EventType.DECLINED, EventType.FAREWELL_DONE, EventType.RESET_REQUESTED):
        context.template_id = None
        context.photos = []
        context.hint = ""
        context.error = ""

    context.state = next_state
    context.revision += 1
