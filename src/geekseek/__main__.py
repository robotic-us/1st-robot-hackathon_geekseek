from __future__ import annotations

import argparse
import asyncio
import json

from .app import build_coordinator
from .config import load_config
from .workflow import EventType, State


async def run_demo(config_path: str) -> None:
    coordinator = build_coordinator(load_config(config_path))
    await coordinator.start()
    print(json.dumps(coordinator.context.as_dict(), ensure_ascii=False))
    await coordinator.emit(EventType.TEMPLATE_SELECTED, template_id="upper_body")
    await coordinator.wait_for_state(State.GUIDING, timeout=5)
    print(json.dumps(coordinator.context.as_dict(), ensure_ascii=False))
    await coordinator.emit(EventType.ALIGNMENT_STABLE)
    await coordinator.wait_for_state(State.REVIEWING, timeout=5)
    print(json.dumps(coordinator.context.as_dict(), ensure_ascii=False))
    await coordinator.emit(EventType.PHOTO_ACCEPTED)
    await coordinator.wait_for_state(State.READY)
    print(json.dumps(coordinator.context.as_dict(), ensure_ascii=False))
    await coordinator.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Geekseek camera robot runtime")
    parser.add_argument("--config", default="config/dev.yaml")
    parser.add_argument("--demo", action="store_true", help="run one headless fake scenario")
    args = parser.parse_args()
    if args.demo:
        asyncio.run(run_demo(args.config))
        return

    import uvicorn

    from .web import create_app

    config = load_config(args.config)
    uvicorn.run(
        create_app(build_coordinator(config)),
        host=config.web.host,
        port=config.web.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
