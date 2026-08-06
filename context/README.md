# context/ — 작업 인계 폴더

이 저장소를 새로 열어보는 사람(또는 다른 에이전트)이 대화 기록 없이도 지금까지의 논의를 따라잡을 수
있도록 정리한 폴더입니다. **처음이면 이 순서로 읽으세요.**

1. [`decisions.md`](decisions.md) — 지금까지 확정된 것 / 아직 열려 있는 것 한 장 요약
2. [`architecture/camera-robot-architecture.html`](architecture/camera-robot-architecture.html) — 전체 소프트웨어 아키텍처 설계 (브라우저로 열어서 볼 것)
3. [`tasks/00-overview.md`](tasks/00-overview.md) — 지금 할 일 4개 트랙과 각 트랙 상세 파일

## 프로젝트 한 줄 요약

Roboticus 로봇 해커톤(2026-08-05~08, KAIST) 참가 프로젝트. phorce SDK(Jetson–pcm–phact 로봇팔) +
iPad 2대 + 엔드이펙터 카메라폰 + C270 웹캠으로 구성된, "핫플레이스"에서 좋은 구도를 골라 자동으로
사진을 찍어주는 로봇. 원래 제안서는 임피던스 제어·직접교시를 실시간 코드로 구현하는 걸 전제했지만,
실제 해커톤 SDK는 참가자 코드에 **①  `/phorce/feedback` 읽기(1kHz)와 ② 미리 저장된 모션 슬롯(1~50)
재생, 이 두 가지만** 허용합니다. 이 제약을 반영해 다시 짠 게 `architecture/` 문서입니다.

## 환경 메모 (Windows → Ubuntu 이어가기)

이 설계는 Windows에서 정리했고, 실제 코드 작업은 Jetson이 있는 **Ubuntu 환경**에서 이어집니다.
- phorce Python 파사드(`import phorce`)와 CLI(`phorce doctor/list/play/status`)는 Jetson에 이미
  설치돼 있습니다 (`reference/sdk-docs/01-quickstart.html` 참고).
- ROS 2 기반이므로 `qos_profile_sensor_data`로 피드백을 구독해야 합니다(`03-manual.html` §6, §11 흔한 실수).
- CAD 원본(iPad 거치대 STL, 로봇팔 STEP)은 용량 문제로 이 저장소엔 아직 커밋하지 않았습니다 — 필요하면
  Git LFS를 붙이거나 별도 공유로 가져오세요. 원본 위치: `사진로봇/cad/`, `CAD/joints.step` (원래 데스크톱 폴더).

## 폴더 구조

```
context/
├── README.md                 ← 지금 이 파일
├── decisions.md               ← 확정/미확정 결정 로그
├── architecture/
│   └── camera-robot-architecture.html   ← 전체 아키텍처 설계 문서(다이어그램 포함)
├── reference/
│   └── sdk-docs/               ← 해커톤 운영진이 배포한 SDK 문서 원본(읽기 전용 자료)
│       ├── 01-quickstart.html
│       ├── 02-tutorial.html
│       ├── 03-manual.html
│       ├── phorce-studio-hackathon-manual.html
│       ├── pcm-board-guide.html
│       ├── hackathon-addendum-p-vector.pdf   (원본명: 해커톤_추가공지_p_vector.pdf)
│       └── ot-hackathon-kickoff.pdf          (원본명: OT_해커톤시작_2026-08-05_최종본)
└── tasks/
    ├── 00-overview.md
    ├── A-robot-motion-loop.md
    ├── B-perception-skeleton.md
    ├── C-eef-camera-shutter.md
    └── D-kiosk-web-server.md
```
