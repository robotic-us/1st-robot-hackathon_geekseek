# 결정 로그

`architecture/camera-robot-architecture.html`의 §2·§10과 팀 논의를 압축한 표. 새 결정이 생기면
여기에 한 줄씩 추가하세요 — 아키텍처 문서 전체를 다시 읽지 않아도 최신 상태를 알 수 있게.

## 확정된 것

| 항목 | 결정 | 근거 |
|---|---|---|
| 참가자 코드가 로봇팔에 할 수 있는 일 | `/phorce/feedback` 읽기(1kHz) + `play(모션ID 1~50)` 재생, 이 두 가지뿐 | `03-manual.html` §1, §12 |
| 직접교시 방식 | 실시간 코드 아님 — phorce Studio GUI로 서보 끄고 손으로 가르쳐 SD카드에 슬롯 저장 | `phorce-studio-hackathon-manual.html` §7 |
| 정밀 카메라 무빙(팬/틸트) | `MotionMap.csv`의 P-Vector `[yd, Ltraj, s0, sd]`를 코드로 직접 생성해서 대체 가능 | `hackathon-addendum-p-vector.pdf` |
| C270 웹캠 역할 | 실시간 인식 전용 센서(사람·포즈·제품 유무). 촬영에는 관여 안 함 | 팀 확인 |
| iPad 1 (가로, 상단) | 얼굴/상태 UI + 구도 템플릿 선택(터치 추가) | 팀 확인 |
| iPad 2 (세로, 하단) | 라이브 프리뷰 + AR 가이드(정렬 안내) + 재촬영 등 키오스크 조작 | 팀 확인 |
| iPad ↔ Jetson 연동 | 네이티브 iOS 앱 없이, Jetson 로컬 웹서버(FastAPI) + iPad Safari 풀스크린(가이드 접근 모드) | 팀 확인 |
| 로봇팔 ↔ iPad 스탠드 | 물리적으로 분리된 별개 장치. 스탠드=고정 감독의 눈, 팔=구도로 움직여 찍는 손 | 팀 확인 |
| 피사체 추적 방식 | 연속 서보잉 대신 이산적 재구도(카테고리 바뀔 때만 슬롯 재생) + 사람이 AR 가이드 보고 스스로 위치 조정 | SDK 제약 + 팀 확인 |
| AR 가이드 구현 방식 | ARKit 네이티브 앱 안 씀 — Jetson이 OpenCV로 스켈레톤+그리드를 프레임에 합성해 MJPEG로 스트리밍 | 팀 확인 |
| 무거운 분할 모델(SAM2/MobileSAM) | 매 프레임 아님 — 정렬 점수 임계값 통과 시 1회 최종 검증 게이트로만 | 팀 확인 |
| 접촉/이상 감지 | `current_a`/`dob_a` 모니터링으로 감지까지만 가능(실시간 순응 불가) → 안전 슬롯 재생으로 대응 | SDK 제약 |
| 접촉 이상 감지 우선순위 | P2로 하향 — 지금은 안 함 | 팀 결정(2026-08-06) |
| ASAP 잔차보정 / 연속 시각서보잉 | 실물에서 이번 대회 범위 밖 — 컨셉 슬라이드로만 | SDK 저수준 접근 불가 |

## 아직 열려 있는 것

| 항목 | 확인 방법 | 담당 트랙 |
|---|---|---|
| 엔드이펙터 폰 기종 (아이폰 vs 안드로이드) | 아이폰 커스텀 미니앱 / Pushcut 웹훅 둘 다 짧게 검증 → 안 되면 안드로이드+IP Webcam으로 전환 | [tasks/C-eef-camera-shutter.md](tasks/C-eef-camera-shutter.md) |
| Jetson·iPad·폰 동일 네트워크 확보 | 현장 Wi-Fi/핫스팟으로 Safari 풀스크린 접속 테스트 | [tasks/D-kiosk-web-server.md](tasks/D-kiosk-web-server.md) |
| 제품 인식 범위 | 손 키포인트 근접도로 단순화 vs 별도 객체 탐지 — §8 파이프라인 자리잡은 뒤 결정 | [tasks/B-perception-skeleton.md](tasks/B-perception-skeleton.md) |
