from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .capture import WebAppCapture
from .coordinator import Coordinator
from .workflow import EventType, State


WEB_ROOT = Path(__file__).resolve().parents[2] / "web"

_VALID_TEMPLATES = {"full_body", "upper_body", "product_closeup"}


def create_app(coordinator: Coordinator) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        await coordinator.start()
        yield
        await coordinator.stop()

    app = FastAPI(title="Geekseek Kiosk", lifespan=lifespan)
    app.state.coordinator = coordinator

    @app.middleware("http")
    async def no_cache_static(request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/static/"):
            # Dev iterates on mock.js/mock.css constantly — a stale cached copy
            # in an already-open kiosk tab looks exactly like a regression.
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response

    app.mount("/static", StaticFiles(directory=WEB_ROOT), name="static")

    if isinstance(coordinator.capture, WebAppCapture):
        capture = coordinator.capture
        capture.save_dir.mkdir(parents=True, exist_ok=True)
        app.mount("/photos", StaticFiles(directory=capture.save_dir), name="photos")

        @app.get("/phone", include_in_schema=False)
        async def phone_page() -> FileResponse:
            return FileResponse(WEB_ROOT / "phone_capture.html")

        @app.websocket("/phone-ws")
        async def phone_ws(websocket: WebSocket) -> None:
            await websocket.accept()
            capture.bind(websocket)
            try:
                while True:
                    data = await websocket.receive_bytes()
                    capture.on_frame(data)
            except WebSocketDisconnect:
                pass
            finally:
                capture.unbind(websocket)

    @app.get("/", include_in_schema=False)
    async def index() -> FileResponse:
        return FileResponse(WEB_ROOT / "debug.html")

    @app.get("/face", include_in_schema=False)
    async def face() -> FileResponse:
        return FileResponse(WEB_ROOT / "face-mock.html")

    @app.get("/guide", include_in_schema=False)
    async def guide() -> FileResponse:
        return FileResponse(WEB_ROOT / "guide-mock.html")

    @app.get("/debug", include_in_schema=False)
    async def debug() -> FileResponse:
        return FileResponse(WEB_ROOT / "debug.html")

    def _mjpeg_stream(get_frame):
        async def stream():
            boundary = b"--frame\r\n"
            while True:
                frame = get_frame()
                if frame:
                    yield boundary + b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
                await asyncio.sleep(0.15)

        return StreamingResponse(
            stream(),
            media_type="multipart/x-mixed-replace; boundary=frame",
            headers={"Cache-Control": "no-cache"},
        )

    if coordinator.person_sensor is not None and hasattr(coordinator.person_sensor, "annotate_jpeg"):

        @app.get("/debug/webcam", include_in_schema=False)
        async def debug_webcam() -> StreamingResponse:
            return _mjpeg_stream(lambda: coordinator.debug_frame)

    if coordinator.person_sensor is not None and hasattr(coordinator.person_sensor, "mirror_jpeg"):

        @app.get("/live/camera", include_in_schema=False)
        async def live_camera() -> StreamingResponse:
            return _mjpeg_stream(lambda: coordinator.live_frame)

    @app.get("/api/state")
    async def get_state() -> dict[str, object]:
        return coordinator.context.as_dict()

    async def emit(event_type: EventType, allowed: set[State], **data: object) -> dict[str, object]:
        if coordinator.context.state not in allowed:
            raise HTTPException(
                status_code=409,
                detail=f"{event_type.value} is invalid in {coordinator.context.state.value}",
            )
        revision = coordinator.context.revision
        await coordinator.emit(event_type, **data)
        await coordinator.wait_for_revision(revision + 1)
        return coordinator.context.as_dict()

    @app.post("/api/capture-started")
    async def capture_started(payload: dict[str, str]) -> dict[str, object]:
        template_id = payload.get("template_id", "")
        if template_id not in _VALID_TEMPLATES:
            raise HTTPException(status_code=422, detail="unknown template_id")
        return await emit(
            EventType.CAPTURE_STARTED,
            {State.DECIDING},
            template_id=template_id,
        )

    @app.post("/api/decline")
    async def decline() -> dict[str, object]:
        return await emit(EventType.DECLINED, {State.DECIDING})

    @app.post("/api/replay")
    async def replay() -> dict[str, object]:
        return await emit(EventType.REPLAY_REQUESTED, {State.ASKING})

    @app.post("/api/liked")
    async def liked() -> dict[str, object]:
        return await emit(EventType.PHOTO_LIKED, {State.ASKING})

    @app.post("/api/reset")
    async def reset() -> dict[str, object]:
        return await emit(EventType.RESET_REQUESTED, {State.ERROR})

    @app.post("/api/debug/position-reached", include_in_schema=False)
    async def debug_position_reached() -> dict[str, object]:
        # Forces guiding->capturing without waiting for the webcam to see
        # someone centered — handy for testing the countdown/burst UI without
        # a person in front of the camera.
        return await emit(EventType.POSITION_REACHED, {State.GUIDING})

    @app.get("/events")
    async def events() -> StreamingResponse:
        async def stream():
            async for snapshot in coordinator.updates():
                yield f"event: state\ndata: {json.dumps(snapshot, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.get("/api/fake-photo/{number}.svg", include_in_schema=False)
    async def fake_photo(number: int) -> Response:
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="900" height="1200" viewBox="0 0 900 1200">
<defs><linearGradient id="g" x2="1" y2="1"><stop stop-color="#17213c"/><stop offset="1" stop-color="#4f2b65"/></linearGradient></defs>
<rect width="900" height="1200" fill="url(#g)"/><circle cx="450" cy="390" r="125" fill="#f4c7a1"/>
<path d="M220 1040 Q260 600 450 600 Q640 600 680 1040" fill="#ff725e"/>
<rect x="55" y="55" width="790" height="1090" rx="30" fill="none" stroke="#fff" stroke-width="8" opacity=".7"/>
<text x="450" y="1100" fill="white" font-family="sans-serif" font-size="42" text-anchor="middle">FAKE CAPTURE #{number}</text>
</svg>"""
        return Response(svg, media_type="image/svg+xml")

    return app
