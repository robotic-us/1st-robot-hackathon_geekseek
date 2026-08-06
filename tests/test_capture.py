import asyncio
import unittest

from geekseek.capture import WebAppCapture


class FakeSocket:
    def __init__(self) -> None:
        self.sent: list[str] = []

    async def send_text(self, data: str) -> None:
        self.sent.append(data)


class WebAppCaptureTests(unittest.IsolatedAsyncioTestCase):
    async def test_capture_without_phone_raises(self) -> None:
        capture = WebAppCapture(save_dir=None)  # type: ignore[arg-type]
        with self.assertRaises(RuntimeError):
            await capture.capture()

    async def test_capture_triggers_and_saves_returned_frame(self) -> None:
        capture = WebAppCapture(save_dir=self._tmp_dir())
        socket = FakeSocket()
        capture.bind(socket)

        async def deliver_frame() -> None:
            await asyncio.sleep(0)
            capture.on_frame(b"jpeg-bytes")

        asyncio.ensure_future(deliver_frame())
        result = await capture.capture()

        self.assertEqual(socket.sent, ["capture"])
        self.assertEqual(result.photo_url, "/photos/phone_1.jpg")
        self.assertEqual((capture.save_dir / "phone_1.jpg").read_bytes(), b"jpeg-bytes")

    async def test_capture_times_out_if_no_frame_arrives(self) -> None:
        capture = WebAppCapture(save_dir=self._tmp_dir(), timeout_seconds=0.05)
        capture.bind(FakeSocket())
        with self.assertRaises(asyncio.TimeoutError):
            await capture.capture()

    async def test_unbind_ignores_stale_socket(self) -> None:
        capture = WebAppCapture(save_dir=self._tmp_dir())
        first, second = FakeSocket(), FakeSocket()
        capture.bind(first)
        capture.bind(second)
        capture.unbind(first)
        self.assertTrue(capture.connected)
        capture.unbind(second)
        self.assertFalse(capture.connected)

    def _tmp_dir(self):
        import tempfile
        from pathlib import Path

        return Path(tempfile.mkdtemp())


if __name__ == "__main__":
    unittest.main()
