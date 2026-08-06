from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class State(str, Enum):
    BOOTING = "booting"
    READY = "ready"
    REPOSITIONING = "repositioning"
    GUIDING = "guiding"
    VERIFYING = "verifying"
    CAPTURING = "capturing"
    REVIEWING = "reviewing"
    ERROR = "error"


class EventType(str, Enum):
    SYSTEM_READY = "system_ready"
    TEMPLATE_SELECTED = "template_selected"
    ROBOT_COMPLETED = "robot_completed"
    ROBOT_FAILED = "robot_failed"
    ALIGNMENT_STABLE = "alignment_stable"
    VERIFICATION_PASSED = "verification_passed"
    VERIFICATION_FAILED = "verification_failed"
    CAPTURE_SUCCEEDED = "capture_succeeded"
    CAPTURE_FAILED = "capture_failed"
    RETAKE_REQUESTED = "retake_requested"
    PHOTO_ACCEPTED = "photo_accepted"
    RESET_REQUESTED = "reset_requested"


@dataclass(frozen=True)
class Event:
    type: EventType
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowContext:
    state: State = State.BOOTING
    template_id: str | None = None
    photo_url: str | None = None
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
    (State.BOOTING, EventType.SYSTEM_READY): State.READY,
    (State.READY, EventType.TEMPLATE_SELECTED): State.REPOSITIONING,
    (State.REPOSITIONING, EventType.ROBOT_COMPLETED): State.GUIDING,
    (State.REPOSITIONING, EventType.ROBOT_FAILED): State.ERROR,
    (State.GUIDING, EventType.ALIGNMENT_STABLE): State.VERIFYING,
    (State.VERIFYING, EventType.VERIFICATION_PASSED): State.CAPTURING,
    (State.VERIFYING, EventType.VERIFICATION_FAILED): State.GUIDING,
    (State.CAPTURING, EventType.CAPTURE_SUCCEEDED): State.REVIEWING,
    (State.CAPTURING, EventType.CAPTURE_FAILED): State.ERROR,
    (State.REVIEWING, EventType.RETAKE_REQUESTED): State.GUIDING,
    (State.REVIEWING, EventType.PHOTO_ACCEPTED): State.READY,
    (State.ERROR, EventType.RESET_REQUESTED): State.READY,
}


def apply_event(context: WorkflowContext, event: Event) -> None:
    """Apply one valid event. The coordinator is the sole caller in production."""
    try:
        next_state = _TRANSITIONS[(context.state, event.type)]
    except KeyError as exc:
        raise InvalidTransition(f"{event.type.value} is invalid in {context.state.value}") from exc

    if event.type is EventType.TEMPLATE_SELECTED:
        template_id = str(event.data.get("template_id", "")).strip()
        if not template_id:
            raise InvalidTransition("template_id is required")
        context.template_id = template_id
        context.photo_url = None
        context.hint = ""
    elif event.type is EventType.VERIFICATION_FAILED:
        context.hint = str(event.data.get("hint", "구도를 다시 맞춰 주세요."))
    elif event.type is EventType.CAPTURE_SUCCEEDED:
        context.photo_url = str(event.data["photo_url"])
    elif event.type in (EventType.ROBOT_FAILED, EventType.CAPTURE_FAILED):
        context.error = str(event.data.get("reason", "unknown error"))
    elif event.type in (EventType.PHOTO_ACCEPTED, EventType.RESET_REQUESTED):
        context.template_id = None
        context.photo_url = None
        context.hint = ""
        context.error = ""

    context.state = next_state
    context.revision += 1
