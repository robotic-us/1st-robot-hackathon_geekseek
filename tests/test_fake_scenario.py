import unittest

from geekseek.capture import FakeCapture
from geekseek.coordinator import Coordinator
from geekseek.robot import FakeRobot
from geekseek.verification import LocalVerifier, VerificationResult
from geekseek.workflow import EventType, State


class RejectOnceVerifier:
    def __init__(self) -> None:
        self.calls = 0

    async def verify(self, frame, context):
        self.calls += 1
        if self.calls == 1:
            return VerificationResult(False, hint="조금 뒤로 이동")
        return VerificationResult(True)


class FakeScenarioTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.robot = FakeRobot(0)
        self.capture = FakeCapture(0)
        self.coordinator = Coordinator(self.robot, self.capture, LocalVerifier())
        await self.coordinator.start()

    async def asyncTearDown(self) -> None:
        await self.coordinator.stop()

    async def test_full_flow_and_retake(self) -> None:
        await self.coordinator.emit(EventType.TEMPLATE_SELECTED, template_id="upper_body")
        await self.coordinator.wait_for_state(State.GUIDING)
        self.assertEqual(self.robot.moves, ["frame.upper_body"])

        await self.coordinator.emit(EventType.ALIGNMENT_STABLE)
        await self.coordinator.wait_for_state(State.REVIEWING)
        first_photo = self.coordinator.context.photo_url

        await self.coordinator.emit(EventType.RETAKE_REQUESTED)
        await self.coordinator.wait_for_state(State.GUIDING)
        await self.coordinator.emit(EventType.ALIGNMENT_STABLE)
        await self.coordinator.wait_for_state(State.REVIEWING)
        self.assertNotEqual(first_photo, self.coordinator.context.photo_url)

        await self.coordinator.emit(EventType.PHOTO_ACCEPTED)
        await self.coordinator.wait_for_state(State.READY)

    async def test_verifier_can_return_to_guiding_without_changing_workflow(self) -> None:
        await self.coordinator.stop()
        self.coordinator = Coordinator(self.robot, self.capture, RejectOnceVerifier())
        await self.coordinator.start()
        await self.coordinator.emit(EventType.TEMPLATE_SELECTED, template_id="full_body")
        await self.coordinator.wait_for_state(State.GUIDING)
        revision = self.coordinator.context.revision
        await self.coordinator.emit(EventType.ALIGNMENT_STABLE)
        await self.coordinator.wait_for_revision(revision + 2)
        self.assertEqual(self.coordinator.context.state, State.GUIDING)
        self.assertEqual(self.coordinator.context.hint, "조금 뒤로 이동")

        await self.coordinator.emit(EventType.ALIGNMENT_STABLE)
        await self.coordinator.wait_for_state(State.REVIEWING)
