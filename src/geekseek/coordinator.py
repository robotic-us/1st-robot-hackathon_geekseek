from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any, Coroutine

from .capture import CaptureDevice
from .robot import Robot, pose_for_template
from .verification import Verifier
from .workflow import Event, EventType, InvalidTransition, State, WorkflowContext, apply_event


class Coordinator:
    """Single writer for workflow state and owner of background effects."""

    def __init__(self, robot: Robot, capture: CaptureDevice, verifier: Verifier) -> None:
        self.context = WorkflowContext()
        self.robot = robot
        self.capture = capture
        self.verifier = verifier
        self.events: asyncio.Queue[Event | None] = asyncio.Queue()
        self._runner: asyncio.Task[None] | None = None
        self._effects: set[asyncio.Task[None]] = set()
        self._subscribers: set[asyncio.Queue[dict[str, object]]] = set()

    async def start(self) -> None:
        if self._runner is not None:
            return
        self._runner = asyncio.create_task(self._run())
        await self.emit(EventType.SYSTEM_READY)
        await self.wait_for_state(State.READY)

    async def stop(self) -> None:
        if self._runner is None:
            return
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
            if self.context.state is State.REPOSITIONING:
                self._spawn(self._move_robot())
            elif self.context.state is State.VERIFYING:
                self._spawn(self._verify())
            elif self.context.state is State.CAPTURING:
                self._spawn(self._capture())

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

    async def _move_robot(self) -> None:
        try:
            await self.robot.move_to(pose_for_template(self.context.template_id or ""))
        except Exception as exc:
            await self.emit(EventType.ROBOT_FAILED, reason=str(exc))
        else:
            await self.emit(EventType.ROBOT_COMPLETED)

    async def _verify(self) -> None:
        try:
            result = await self.verifier.verify(None, self.context)
        except Exception as exc:
            await self.emit(EventType.VERIFICATION_FAILED, hint=str(exc))
            return
        if result.passed:
            await self.emit(EventType.VERIFICATION_PASSED)
        else:
            await self.emit(EventType.VERIFICATION_FAILED, hint=result.hint, reason=result.reason)

    async def _capture(self) -> None:
        try:
            result = await self.capture.capture()
        except Exception as exc:
            await self.emit(EventType.CAPTURE_FAILED, reason=str(exc))
        else:
            await self.emit(EventType.CAPTURE_SUCCEEDED, photo_url=result.photo_url)
