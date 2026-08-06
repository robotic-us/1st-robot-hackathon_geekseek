import unittest

from geekseek.workflow import Event, EventType, InvalidTransition, State, WorkflowContext, apply_event


class WorkflowTests(unittest.TestCase):
    def test_happy_path(self) -> None:
        context = WorkflowContext()
        events = [
            Event(EventType.SYSTEM_READY),
            Event(EventType.TEMPLATE_SELECTED, {"template_id": "upper_body"}),
            Event(EventType.ROBOT_COMPLETED),
            Event(EventType.ALIGNMENT_STABLE),
            Event(EventType.VERIFICATION_PASSED),
            Event(EventType.CAPTURE_SUCCEEDED, {"photo_url": "/photo.jpg"}),
            Event(EventType.PHOTO_ACCEPTED),
        ]
        for event in events:
            apply_event(context, event)

        self.assertEqual(context.state, State.READY)
        self.assertIsNone(context.template_id)
        self.assertIsNone(context.photo_url)
        self.assertEqual(context.revision, len(events))

    def test_rejects_event_from_wrong_state(self) -> None:
        with self.assertRaises(InvalidTransition):
            apply_event(WorkflowContext(), Event(EventType.ALIGNMENT_STABLE))

    def test_verification_failure_returns_to_guiding(self) -> None:
        context = WorkflowContext(state=State.VERIFYING)
        apply_event(context, Event(EventType.VERIFICATION_FAILED, {"hint": "왼쪽으로 이동"}))
        self.assertEqual(context.state, State.GUIDING)
        self.assertEqual(context.hint, "왼쪽으로 이동")
