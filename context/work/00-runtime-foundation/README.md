# 트랙 0 — 런타임 공통 기반

## 목표

로봇·Jetson 없이도 구도 선택→가이드→정렬→촬영→리뷰→재촬영/확정 흐름이 끝까지 실행되는
단일 Python 애플리케이션 기반을 만든다. B·C·D 트랙은 이 기반 위에 실제 구현체를 연결하고, A 트랙은
마지막에 `FakeRobot`을 `PhorceRobot`으로 교체한다.

구현 기준은 [`../../knowledge/architecture/runtime-architecture.md`](../../knowledge/architecture/runtime-architecture.md)를
따른다.

## 현재 상태

`설계 완료 · 구현 전`

## 구현 범위

1. `pyproject.toml`, `src/geekseek/`, `config/`, `tests/` 최소 뼈대
2. `workflow.py`의 상태·이벤트·컨텍스트·전이 규칙
3. `Coordinator`와 단일 `asyncio.Queue`
4. `FakeRobot`, `FakeCapture`, fake/녹화 영상 입력
5. FastAPI `/face`, `/guide`, `/events`, `/stream.mjpg` 최소 라우트
6. fake 전체 시나리오 통합 테스트

## 완료 기준

- `python -m geekseek --config config/dev.yaml` 한 명령으로 실행된다.
- 모든 상태 전이가 단위 테스트로 검증된다.
- 브라우저에서 구도를 선택하면 fake 로봇 이동 후 가이드 상태로 넘어간다.
- fake 정렬 완료 후 샘플 사진이 리뷰 화면에 표시된다.
- 재촬영은 `GUIDING`, 사진 확정은 `READY`로 되돌아간다.
- FastAPI·OpenCV·ROS 구현이 `workflow.py`에 침투하지 않는다.

## 진행 기록

구조나 인터페이스 결정이 바뀌면 런타임 아키텍처 문서와
[`../../knowledge/decisions.md`](../../knowledge/decisions.md)를 함께 갱신한다. 구현 진전은
[`NOTES.md`](NOTES.md)와 [`../../progress/`](../../progress/)에 기록한다.
