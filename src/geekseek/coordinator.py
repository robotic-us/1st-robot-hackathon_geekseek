from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable
from typing import Any, Coroutine

from .capture import CaptureDevice
from .perception import PersonSensor, PersonSignal, encode_jpeg, is_approaching, is_positioned, is_ready_signal
from .robot import Robot, burst_poses_for_template
from .vlm import Greeter
from .workflow import Event, EventType, InvalidTransition, State, WorkflowContext, apply_event

FrameSource = Callable[[], object | None]


class Coordinator:
    """Single writer for workflow state and owner of background effects."""

    def __init__(
        self,
        robot: Robot,
        capture: CaptureDevice,
        person_sensor: PersonSensor | None = None,
        frame_source: FrameSource | None = None,
        greeter: Greeter | None = None,
        sense_interval: float = 0.2,
        greeting_seconds: float = 3.0,
        preview_seconds: float = 3.0,
        farewell_seconds: float = 4.0,
        countdown_seconds: float = 0.7,
        ready_timeout_seconds: float = 12.0,
    ) -> None:
        self.context = WorkflowContext()
        self.robot = robot
        self.capture = capture
        self.person_sensor = person_sensor
        self.frame_source = frame_source
        self.greeter = greeter
        self.sense_interval = sense_interval
        self.greeting_seconds = greeting_seconds
        self.preview_seconds = preview_seconds
        self.farewell_seconds = farewell_seconds
        self.countdown_seconds = countdown_seconds
        self.ready_timeout_seconds = ready_timeout_seconds
        self.debug_frame: bytes | None = None
        self.live_frame: bytes | None = None
        self.events: asyncio.Queue[Event | None] = asyncio.Queue()
        self._runner: asyncio.Task[None] | None = None
        self._sense_task: asyncio.Task[None] | None = None
        self._effects: set[asyncio.Task[None]] = set()
        self._subscribers: set[asyncio.Queue[dict[str, object]]] = set()
        self._ready_event = asyncio.Event()

    async def start(self) -> None:
        if self._runner is not None:
            return
        self._runner = asyncio.create_task(self._run())
        if self.person_sensor is not None:
            self._sense_task = asyncio.create_task(self._sense_loop())
        await self.emit(EventType.SYSTEM_READY)
        await self.wait_for_state(State.WAITING)

    async def stop(self) -> None:
        if self._runner is None:
            return
        if self._sense_task is not None:
            self._sense_task.cancel()
            await asyncio.gather(self._sense_task, return_exceptions=True)
            self._sense_task = None
        for task in self._effects:
            task.cancel()
        if self._effects:
            await asyncio.gather(*self._effects, return_exceptions=True)
        self._effects.clear()
        await self.events.put(None)
        await self._runner
        self._runner = None

    async def emit(self, event_type: EventType, **data: object) -> None:
        await self.events.put(Event(event_type, data))

    async def wait_for_state(self, state: State, timeout: float = 2.0) -> None:
        await asyncio.wait_for(self._wait_for_state(state), timeout)

    async def _wait_for_state(self, state: State) -> None:
        while self.context.state is not state:
            await asyncio.sleep(0.005)

    async def wait_for_revision(self, revision: int, timeout: float = 2.0) -> None:
        await asyncio.wait_for(self._wait_for_revision(revision), timeout)

    async def _wait_for_revision(self, revision: int) -> None:
        while self.context.revision < revision:
            await asyncio.sleep(0.005)

    async def updates(self) -> AsyncIterator[dict[str, object]]:
        queue: asyncio.Queue[dict[str, object]] = asyncio.Queue(maxsize=1)
        self._subscribers.add(queue)
        try:
            yield self.context.as_dict()
            while True:
                yield await queue.get()
        finally:
            self._subscribers.discard(queue)

    async def _run(self) -> None:
        while (event := await self.events.get()) is not None:
            try:
                apply_event(self.context, event)
            except InvalidTransition:
                continue
            self._publish()
            if self.context.state is State.GREETING:
                self._spawn(self._timer(EventType.GREETING_DONE, self.greeting_seconds))
                if self.greeter is not None:
                    self._spawn(self._generate_greeting())
            elif self.context.state is State.CAPTURING:
                self._spawn(self._capture_burst())
            elif self.context.state is State.PREVIEWING:
                self._spawn(self._timer(EventType.PREVIEW_DONE, self.preview_seconds))
            elif self.context.state is State.FAREWELL:
                self._spawn(self._timer(EventType.FAREWELL_DONE, self.farewell_seconds))

    def _spawn(self, coroutine: Coroutine[Any, Any, None]) -> None:
        task = asyncio.create_task(coroutine)
        self._effects.add(task)
        task.add_done_callback(self._effects.discard)

    def _publish(self) -> None:
        snapshot = self.context.as_dict()
        for queue in self._subscribers:
            if queue.full():
                queue.get_nowait()
            queue.put_nowait(snapshot)

    async def _timer(self, event_type: EventType, seconds: float) -> None:
        await asyncio.sleep(seconds)
        await self.emit(event_type)

    async def _sense_loop(self) -> None:
        """Runs for the whole session; only acts when the current state cares
        about a person signal (WAITING → 접근 감지, GUIDING → 정위치 확인)."""
        while True:
            await asyncio.sleep(self.sense_interval)
            if self.person_sensor is None:
                continue
            if self.frame_source is not None:
                frame = self.frame_source()
                if frame is None:
                    continue  # webcam hasn't produced a first frame yet
            else:
                frame = None
            signal: PersonSignal = self.person_sensor.sense(frame)
            approaching = is_approaching(signal)
            positioned = is_positioned(signal)
            if hasattr(self.person_sensor, "annotate_jpeg"):
                self.debug_frame = self.person_sensor.annotate_jpeg(frame, signal, approaching, positioned)
            if hasattr(self.person_sensor, "mirror_jpeg"):
                self.live_frame = self.person_sensor.mirror_jpeg(frame)
            if self.context.state is State.WAITING and approaching:
                await self.emit(EventType.PERSON_APPROACHED)
            elif self.context.state is State.GUIDING and positioned:
                await self.emit(EventType.POSITION_REACHED)
            elif (
                self.context.state is State.CAPTURING
                and self.context.awaiting_ready
                and is_ready_signal(signal)
            ):
                self._ready_event.set()

    async def _generate_greeting(self) -> None:
        """Fire-and-forget VLM caption for the greeting caption. Never blocks
        the timer-driven GREETING_DONE transition; applies the result only if
        the cycle hasn't already moved past deciding (stale response guard)."""
        if self.greeter is None or self.frame_source is None:
            return
        frame = self.frame_source()
        if frame is None:
            return
        jpeg = encode_jpeg(frame)
        if not jpeg:
            return
        line = await self.greeter.greet(jpeg)
        if line and self.context.state in (State.GREETING, State.DECIDING):
            self._patch(greeting_line=line)

    async def _wait_until_ready(self) -> None:
        """정위치 도달 직후, 카운트다운 전에 "손 들어 준비완료" 신호를 기다린다.
        person_sensor가 없으면(테스트/시뮬레이션) 곧바로 통과. _sense_loop가
        awaiting_ready=True인 동안 is_ready_signal을 감지하면 _ready_event를
        세팅한다 — 여기서 프레임을 직접 sense()하지 않아 중복 추론을 피한다."""
        if self.person_sensor is None:
            return
        self._ready_event.clear()
        self._patch(awaiting_ready=True)
        try:
            await asyncio.wait_for(self._ready_event.wait(), self.ready_timeout_seconds)
        except asyncio.TimeoutError:
            pass  # 손을 못 들었어도 계속 기다리게 하지 않고 진행 (fail-safe)
        self._patch(awaiting_ready=False)

    async def _capture_burst(self) -> None:
        await self._wait_until_ready()

        for remaining in (3, 2, 1):
            self._patch(countdown=remaining)
            await asyncio.sleep(self.countdown_seconds)
        self._patch(countdown=None)

        photos: list[str] = []
        try:
            for pose in burst_poses_for_template(self.context.template_id or ""):
                await self.robot.move_to(pose)
                result = await self.capture.capture()
                photos.append(result.photo_url)
                # Publish after every shot (not just at the end) so the guide
                # screen can flash each captured frame as it lands instead of
                # only jumping from 0 to 3 at burst completion.
                self._patch(photos=list(photos))
        except Exception as exc:
            await self.emit(EventType.CAPTURE_FAILED, reason=str(exc))
        else:
            await self.emit(EventType.BURST_COMPLETE, photos=photos)

    def _patch(self, **fields: object) -> None:
        """Update context fields directly, outside apply_event, for data that
        isn't a state transition (countdown ticks, in-progress photos) —
        same idea as _generate_greeting's greeting_line update."""
        for key, value in fields.items():
            setattr(self.context, key, value)
        self.context.revision += 1
        self._publish()
