# NOTES — 런타임 공통 기반

자유 형식 작업 메모. 최신 항목이 위로 오도록 추가한다.

---

## 2026-08-06

- FastAPI에 `/face`, `/guide`, `/debug`, `/events`와 구도 선택·수동 정렬·재촬영·확정 API를 추가.
  SSE로 두 화면이 같은 `WorkflowContext`를 실시간 반영하며, fake 사진도 리뷰 화면에 표시.
- 실제 Uvicorn에서 페이지/API 200 응답, `ready → guiding → reviewing` HTTP 흐름, SSE 초기 이벤트를 확인.
- `src/geekseek/`에 순수 상태 전이, 단일 작성자 `Coordinator`, `FakeRobot`, `FakeCapture`,
  `LocalVerifier`를 구현. happy path·재촬영·검증 거절 복귀를 테스트로 고정.
- `assets/cad/Assemble_CAM.step`에 CAD 원본을 포함하고 `ros/geekseek_fake_robot/`에 6관절 primitive
  URDF, 의미 기반 포즈 노드, RViz 설정을 추가.
- ROS 토픽 실검증에서 `frame.upper_body` 명령과 6개 `/joint_states` 값 발행을 확인. `rviz` 프로필로
  상태 머신 전체 흐름도 통과.
- 단일 Python 프로세스, 이벤트 기반 상태 머신, 단일 상태 작성자 구조로 결정.
- 기능을 줄이지 않되 초기 코드는 소수의 책임별 Python 모듈로 시작하기로 결정.
- `VERIFYING`에는 우선 `LocalVerifier`를 연결하고, VLM 성공·거절·타임아웃 fake만 준비한 뒤 실제 API는
  VLM 없는 전체 흐름이 완성된 다음 연결하기로 결정.
- 상세 기준: [`../../knowledge/architecture/runtime-architecture.md`](../../knowledge/architecture/runtime-architecture.md)
