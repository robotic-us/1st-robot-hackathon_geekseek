import unittest

from geekseek.capture import FakeCapture
from geekseek.coordinator import Coordinator
from geekseek.perception import FakePersonSensor, PersonSignal
from geekseek.robot import FakeRobot
from geekseek.workflow import EventType, State


class FakeScenarioTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.robot = FakeRobot(0)
        self.capture = FakeCapture(0)
        self.coordinator = Coordinator(
            self.robot,
            self.capture,
            greeting_seconds=0.05,
            countdown_seconds=0,
            preview_seconds=0.05,
            farewell_seconds=0.05,
        )
        await self.coordinator.start()

    async def asyncTearDown(self) -> None:
        await self.coordinator.stop()

    async def test_full_flow_and_replay(self) -> None:
        await self.coordinator.emit(EventType.PERSON_APPROACHED)
        await self.coordinator.wait_for_state(State.DECIDING)

        await self.coordinator.emit(EventType.CAPTURE_STARTED, template_id="upper_body")
        await self.coordinator.wait_for_state(State.GUIDING)

        await self.coordinator.emit(EventType.POSITION_REACHED)
        await self.coordinator.wait_for_state(State.PREVIEWING)
        self.assertEqual(
            self.robot.moves,
            ["frame.upper_body", "frame.full_body", "frame.product_closeup"],
        )
        first_photos = list(self.coordinator.context.photos)
        self.assertEqual(len(first_photos), 3)

        await self.coordinator.wait_for_state(State.ASKING)
        revision = self.coordinator.context.revision
        await self.coordinator.emit(EventType.REPLAY_REQUESTED)
        # wait_for_state(ASKING) would race here: we're already in ASKING, so a
        # naive poll could return before REPLAY_REQUESTED is even applied. Anchor
        # on the revision bump first so we know the round trip actually happened.
        await self.coordinator.wait_for_revision(revision + 1)
        self.assertEqual(self.coordinator.context.state, State.PREVIEWING)
        await self.coordinator.wait_for_state(State.ASKING)
        self.assertEqual(self.coordinator.context.photos, first_photos)

        await self.coordinator.emit(EventType.PHOTO_LIKED)
        await self.coordinator.wait_for_state(State.WAITING)
        self.assertIsNone(self.coordinator.context.template_id)
        self.assertEqual(self.coordinator.context.photos, [])

    async def test_decline_returns_to_waiting(self) -> None:
        await self.coordinator.emit(EventType.PERSON_APPROACHED)
        await self.coordinator.wait_for_state(State.DECIDING)
        await self.coordinator.emit(EventType.DECLINED)
        await self.coordinator.wait_for_state(State.WAITING)

    async def test_capture_failure_moves_to_error_and_resets(self) -> None:
        class FailingCapture:
            async def capture(self):
                raise RuntimeError("no phone connected")

        await self.coordinator.stop()
        self.coordinator = Coordinator(
            self.robot,
            FailingCapture(),
            greeting_seconds=0.05,
            countdown_seconds=0,
            preview_seconds=0.05,
            farewell_seconds=0.05,
        )
        await self.coordinator.start()

        await self.coordinator.emit(EventType.PERSON_APPROACHED)
        await self.coordinator.wait_for_state(State.DECIDING)
        await self.coordinator.emit(EventType.CAPTURE_STARTED, template_id="full_body")
        await self.coordinator.wait_for_state(State.GUIDING)
        await self.coordinator.emit(EventType.POSITION_REACHED)
        await self.coordinator.wait_for_state(State.ERROR)
        self.assertIn("no phone connected", self.coordinator.context.error)

        await self.coordinator.emit(EventType.RESET_REQUESTED)
        await self.coordinator.wait_for_state(State.WAITING)


class GreetingLineTests(unittest.IsolatedAsyncioTestCase):
    async def test_vlm_greeting_line_applied_during_greeting_and_cleared_on_reset(self) -> None:
        import numpy as np

        from geekseek.vlm import FakePersonalizedGreeter

        frame = np.zeros((4, 4, 3), dtype=np.uint8)
        coordinator = Coordinator(
            FakeRobot(0),
            FakeCapture(0),
            frame_source=lambda: frame,
            greeter=FakePersonalizedGreeter("두 분 잘 어울리세요"),
            greeting_seconds=0.05,
            countdown_seconds=0,
            preview_seconds=0.05,
            farewell_seconds=0.05,
        )
        await coordinator.start()
        try:
            await coordinator.emit(EventType.PERSON_APPROACHED)
            await coordinator.wait_for_state(State.DECIDING)
            await self._wait_until(lambda: coordinator.context.greeting_line is not None)
            self.assertEqual(coordinator.context.greeting_line, "두 분 잘 어울리세요")

            await coordinator.emit(EventType.DECLINED)
            await coordinator.wait_for_state(State.WAITING)
            self.assertIsNone(coordinator.context.greeting_line)
        finally:
            await coordinator.stop()

    async def _wait_until(self, predicate, timeout: float = 2.0) -> None:
        import asyncio
        import time

        deadline = time.monotonic() + timeout
        while not predicate():
            if time.monotonic() > deadline:
                self.fail("condition not met in time")
            await asyncio.sleep(0.005)


class SenseLoopTests(unittest.IsolatedAsyncioTestCase):
    async def test_fake_person_sensor_drives_approach_and_position(self) -> None:
        signals = [
            PersonSignal(detected=False),
            PersonSignal(detected=True, size_ratio=0.2, center_x=0.5, center_y=0.5),
        ]
        coordinator = Coordinator(
            FakeRobot(0),
            FakeCapture(0),
            person_sensor=FakePersonSensor(signals),
            sense_interval=0.01,
            greeting_seconds=0.05,
            countdown_seconds=0,
            preview_seconds=0.05,
            farewell_seconds=0.05,
        )
        await coordinator.start()
        try:
            await coordinator.wait_for_state(State.GREETING, timeout=2)
        finally:
            await coordinator.stop()
