import unittest

from fastapi.testclient import TestClient

from geekseek.capture import FakeCapture
from geekseek.coordinator import Coordinator
from geekseek.robot import FakeRobot
from geekseek.web import create_app
from geekseek.workflow import EventType


class WebTests(unittest.TestCase):
    def setUp(self) -> None:
        self.coordinator = Coordinator(
            FakeRobot(0),
            FakeCapture(0),
            greeting_seconds=0.05,
            countdown_seconds=0,
            preview_seconds=0.05,
            farewell_seconds=0.05,
        )
        self.client_context = TestClient(create_app(self.coordinator))
        self.client = self.client_context.__enter__()
        # PERSON_APPROACHED/POSITION_REACHED are webcam-driven in production (no HTTP
        # route for them); tests reach into the coordinator via the TestClient's portal
        # so the call runs on the same event loop as the app instead of a stray one.
        self._emit(EventType.PERSON_APPROACHED)
        self._wait_for("deciding")

    def tearDown(self) -> None:
        self.client_context.__exit__(None, None, None)

    def _emit(self, event_type: EventType, **data: object) -> None:
        self.client.portal.call(self.coordinator.emit, event_type, **data)

    def test_pages_and_initial_state(self) -> None:
        self.assertEqual(self.client.get("/face").status_code, 200)
        self.assertEqual(self.client.get("/guide").status_code, 200)
        self.assertEqual(self.client.get("/debug").status_code, 200)
        self.assertEqual(self.client.get("/api/state").json()["state"], "deciding")

    def test_full_api_flow(self) -> None:
        self.assertEqual(
            self.client.post("/api/capture-started", json={"template_id": "upper_body"}).status_code,
            200,
        )
        self._wait_for("guiding")

        self._emit(EventType.POSITION_REACHED)
        previewing = self._wait_for("previewing")
        self.assertEqual(len(previewing["photos"]), 3)
        for photo_url in previewing["photos"]:
            self.assertTrue(photo_url.endswith(".svg"))
            self.assertEqual(self.client.get(photo_url).status_code, 200)

        asking = self._wait_for("asking")
        self.assertEqual(self.client.post("/api/replay").status_code, 200)
        self._wait_for("previewing")
        self._wait_for("asking")

        self.assertEqual(self.client.post("/api/liked").status_code, 200)
        farewell = self._wait_for("farewell")
        self.assertEqual(farewell["photos"], asking["photos"])

        waiting = self._wait_for("waiting")
        self.assertEqual(waiting["photos"], [])
        self.assertIsNone(waiting["template_id"])

    def test_decline_returns_to_waiting(self) -> None:
        self.assertEqual(self.client.post("/api/decline").status_code, 200)
        self._wait_for("waiting")

    def test_invalid_action_returns_conflict(self) -> None:
        response = self.client.post("/api/liked")
        self.assertEqual(response.status_code, 409)

    def test_unknown_template_id_rejected(self) -> None:
        response = self.client.post("/api/capture-started", json={"template_id": "bogus"})
        self.assertEqual(response.status_code, 422)

    def _wait_for(self, state: str) -> dict[str, object]:
        for _ in range(200):
            value = self.client.get("/api/state").json()
            if value["state"] == state:
                return value
        self.fail(f"state did not become {state}")


if __name__ == "__main__":
    unittest.main()
