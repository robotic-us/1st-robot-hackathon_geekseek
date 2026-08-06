from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable
from typing import Any, Coroutine

from .capture import CaptureDevice
from .perception import PersonSensor, PersonSignal, is_approaching, is_positioned
from .robot import Robot, burst_poses_for_template
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
        sense_interval: float = 0.2,
        greeting_seconds: float = 3.0,
        preview_seconds: float = 3.0,
        farewell_seconds: float = 4.0,
    ) -> None:
        self.context = WorkflowContext()
        self.robot = robot
        self.capture = capture
        self.person_sensor = person_sensor
        self.frame_source = frame_source
        self.sense_interval = sense_interval
        self.greeting_seconds = greeting_seconds
        self.preview_seconds = preview_seconds
        self.farewell_seconds = farewell_seconds
        self.debug_frame: bytes | None = None
        self.live_frame: bytes | None = None
        self.events: asyncio.Queue[Event | None] = asyncio.Queue()
        self._runner: asyncio.Task[None] | None = None
        self._sense_task: asyncio.Task[None] | None = None
        self._effects: set[asyncio.Task[None]] = set()
        self._subscribers: set[asyncio.Queue[dict[str, object]]] = set()

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

    async def _capture_burst(self) -> None:
        photos: list[str] = []
        try:
            for pose in burst_poses_for_template(self.context.template_id or ""):
                await self.robot.move_to(pose)
                result = await self.capture.capture()
                photos.append(result.photo_url)
        except Exception as exc:
            await self.emit(EventType.CAPTURE_FAILED, reason=str(exc))
        else:
            await self.emit(EventType.BURST_COMPLETE, photos=photos)
