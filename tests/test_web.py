import unittest

from fastapi.testclient import TestClient

from geekseek.capture import FakeCapture
from geekseek.coordinator import Coordinator
from geekseek.robot import FakeRobot
from geekseek.verification import LocalVerifier
from geekseek.web import create_app


class WebTests(unittest.TestCase):
    def setUp(self) -> None:
        coordinator = Coordinator(FakeRobot(0), FakeCapture(0), LocalVerifier())
        self.client_context = TestClient(create_app(coordinator))
        self.client = self.client_context.__enter__()

    def tearDown(self) -> None:
        self.client_context.__exit__(None, None, None)

    def test_pages_and_initial_state(self) -> None:
        self.assertEqual(self.client.get("/face").status_code, 200)
        self.assertEqual(self.client.get("/guide").status_code, 200)
        self.assertEqual(self.client.get("/debug").status_code, 200)
        self.assertEqual(self.client.get("/api/state").json()["state"], "ready")

    def test_full_api_flow(self) -> None:
        self.assertEqual(self.client.post("/api/template/upper_body").status_code, 200)
        self._wait_for("guiding")
        self.assertEqual(self.client.post("/api/alignment-ready").status_code, 200)
        reviewing = self._wait_for("reviewing")
        self.assertTrue(reviewing["photo_url"].endswith(".svg"))
        self.assertEqual(self.client.get(reviewing["photo_url"]).status_code, 200)
        self.assertEqual(self.client.post("/api/accept").status_code, 200)
        self.assertEqual(self._wait_for("ready")["state"], "ready")

    def test_invalid_action_returns_conflict(self) -> None:
        response = self.client.post("/api/alignment-ready")
        self.assertEqual(response.status_code, 409)

    def _wait_for(self, state: str) -> dict[str, object]:
        for _ in range(100):
            value = self.client.get("/api/state").json()
            if value["state"] == state:
                return value
        self.fail(f"state did not become {state}")
