# 현재 상태 (한눈에)

> 이 파일은 **지금 스냅샷**입니다 — 과거 기록이 아니라 최신 상태로 계속 덮어써서 유지하세요.
> 시간 흐름에 따른 기록은 [`log/`](log/)에 날짜별로 남깁니다.

**마지막 갱신**: 2026-08-06

## 요약
물리 구성(C270=인식 전용, iPad1=구도선택 UI, iPad2=AR가이드+키오스크, iPad↔Jetson=로컬 웹서버) 확정.
상위 설계에 따라 런타임 구현 시작. 이벤트 상태 머신·`Coordinator`·`FakeRobot`·`FakeCapture`·
`LocalVerifier`의 headless 전체 흐름과 테스트를 구현했고, STEP 원본 및 RViz 6관절 fake robot을 추가했다.
FastAPI/SSE에 iPad 1 구도 선택, iPad 2 가이드·리뷰, PC 디버그 화면까지 연결했다. Pose·MJPEG·실제 폰
촬영은 아직 연결 전이다.

## 트랙별 상태

| 트랙 | 상태 | 비고 |
|---|---|---|
| [0. 런타임 공통 기반](../work/00-runtime-foundation/README.md) | 🟡 진행 중 | 코어·RViz·iPad fake 흐름 완료, 영상 연결이 다음 |
| [A. 로봇 최소 왕복](../work/A-robot-motion-loop/README.md) | 🔴 시작 전 | P0 게이트 — 가장 먼저 되어야 함 |
| [B. 스켈레톤 인식](../work/B-perception-skeleton/README.md) | 🔴 시작 전 | 로봇 없이 지금 바로 착수 가능 |
| [C. 엔드이펙터 폰 셔터](../work/C-eef-camera-shutter/README.md) | 🔴 시작 전 | 아이폰 vs 안드로이드 — 오늘 결정 필요 |
| [D. 키오스크 웹서버](../work/D-kiosk-web-server/README.md) | 🟡 진행 중 | 서버·SSE·화면 완료, 실기기/MJPEG 확인 필요 |

(🔴 시작 전 · 🟡 진행 중 · 🟢 완료 · ⚠️ 막힘)

## 지금 막혀 있는 것
없음.

## 다음 체크인 때 확인할 것
- 실제 iPad 2대에서 `/face`, `/guide`, SSE 동기화를 확인할 것
- VLM이 꺼진 `LocalVerifier` 전체 흐름과 fake VLM 성공·거절·타임아웃 테스트가 분리돼 있는지
- D의 MJPEG 영상 스트림을 iPad 2 `viewfinder`에 연결할 것
- 트랙 C(폰 기종) 결정됐는지 → [`../knowledge/decisions.md`](../knowledge/decisions.md) "아직 열려 있는 것" 갱신됐는지
- 트랙 A가 sim에서라도 `play()` 왕복에 성공했는지
