from __future__ import annotations

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


def create_app(coordinator: Coordinator) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        await coordinator.start()
        yield
        await coordinator.stop()

    app = FastAPI(title="Geekseek Kiosk", lifespan=lifespan)
    app.state.coordinator = coordinator
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
        return FileResponse(WEB_ROOT / "face.html")

    @app.get("/guide", include_in_schema=False)
    async def guide() -> FileResponse:
        return FileResponse(WEB_ROOT / "guide.html")

    @app.get("/debug", include_in_schema=False)
    async def debug() -> FileResponse:
        return FileResponse(WEB_ROOT / "debug.html")

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

    @app.post("/api/template/{template_id}")
    async def select_template(template_id: str) -> dict[str, object]:
        if template_id not in {"full_body", "upper_body", "product_closeup"}:
            raise HTTPException(status_code=404, detail="unknown template")
        return await emit(
            EventType.TEMPLATE_SELECTED,
            {State.READY},
            template_id=template_id,
        )

    @app.post("/api/alignment-ready")
    async def alignment_ready() -> dict[str, object]:
        return await emit(EventType.ALIGNMENT_STABLE, {State.GUIDING})

    @app.post("/api/retake")
    async def retake() -> dict[str, object]:
        return await emit(EventType.RETAKE_REQUESTED, {State.REVIEWING})

    @app.post("/api/accept")
    async def accept() -> dict[str, object]:
        return await emit(EventType.PHOTO_ACCEPTED, {State.REVIEWING})

    @app.post("/api/reset")
    async def reset() -> dict[str, object]:
        return await emit(EventType.RESET_REQUESTED, {State.ERROR})

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
