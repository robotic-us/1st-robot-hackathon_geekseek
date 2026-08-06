# 현재 상태 (한눈에)

> 이 파일은 **지금 스냅샷**입니다 — 과거 기록이 아니라 최신 상태로 계속 덮어써서 유지하세요.
> 시간 흐름에 따른 기록은 [`log/`](log/)에 날짜별로 남깁니다.

**마지막 갱신**: 2026-08-06

## 요약
물리 구성(C270=인식 전용, iPad1=구도선택 UI, iPad2=AR가이드+키오스크, iPad↔Jetson=로컬 웹서버) 확정.
소프트웨어 아키텍처 설계 완료. Windows에서 Ubuntu/Jetson 환경으로 작업 이전 준비 — 아직 코드는
없음. 4개 트랙으로 나눠 병렬 착수 예정.

## 트랙별 상태

| 트랙 | 상태 | 비고 |
|---|---|---|
| [A. 로봇 최소 왕복](../work/A-robot-motion-loop/README.md) | 🔴 시작 전 | P0 게이트 — 가장 먼저 되어야 함 |
| [B. 스켈레톤 인식](../work/B-perception-skeleton/README.md) | 🔴 시작 전 | 로봇 없이 지금 바로 착수 가능 |
| [C. 엔드이펙터 폰 셔터](../work/C-eef-camera-shutter/README.md) | 🔴 시작 전 | 아이폰 vs 안드로이드 — 오늘 결정 필요 |
| [D. 키오스크 웹서버](../work/D-kiosk-web-server/README.md) | 🔴 시작 전 | 네트워크 리스크 조기 발견용 |

(🔴 시작 전 · 🟡 진행 중 · 🟢 완료 · ⚠️ 막힘)

## 지금 막혀 있는 것
없음.

## 다음 체크인 때 확인할 것
- 트랙 C(폰 기종) 결정됐는지 → [`../knowledge/decisions.md`](../knowledge/decisions.md) "아직 열려 있는 것" 갱신됐는지
- 트랙 A가 sim에서라도 `play()` 왕복에 성공했는지
