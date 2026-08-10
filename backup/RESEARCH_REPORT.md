# RPI Research Report — AI 인생샷 촬영 로봇

- 조사일: 2026-08-06 (Asia/Seoul)
- 조사 범위: 이 저장소에 존재하는 문서, 실행파일, 메시/CAD, 이미지, 논문, 프레젠테이션
- 제외 범위: 코드 구현, CAD 수정, 실물 구동, 외부 웹 검색
- 판정 태그:
  - `NEEDS_VERIFICATION`: 저장소 안 근거가 불완전하거나 서로 충돌함
  - `NOT_FOUND_IN_REPOSITORY`: 필요한 자료가 저장소에 없음
  - `REQUIRES_HARDWARE_TEST`: 실물에서만 확인 가능함
  - `REQUIRES_ORGANIZER_CONFIRMATION`: 비공개 인터페이스 또는 운영진 권한이 필요함

## 0. 결론 요약

### 핵심 결론

1. **현재 저장소만으로는 제작된 하드웨어가 목표 촬영 동작을 수행할 수 있다고 확정할 수 없다.**
   - 실제 조립 사진, 클램프 CAD, 스마트폰 홀더 CAD, STEP/3MF/원본 조립 CAD, 관절 한계, 링크 질량, 케이블 배치가 없다.
   - `joints.stl`에서 식별되는 phact 중심은 5개이며 중립 자세의 추정 축 배열은 `Z–Y–Y–Y–Z`이다. 지급품은 6개이고 콘셉트 렌더는 J1~J6을 표시한다. 6번째 축의 실제 위치는 `NEEDS_VERIFICATION`이다.
   - `joints.stl`은 테이블 클램프가 아니라 네 방향 발이 있는 바닥/플랫폼형 베이스를 포함한다. 프롬프트의 현재 클램프형 구조는 `NOT_FOUND_IN_REPOSITORY`이다.

2. **Jetson 참가자용 하행 제어는 저장된 모션 슬롯 재생으로 제한된다.**
   - 읽기: `/phorce/feedback`, 12축 배열, 1 kHz, ROS 2 sensor-data QoS.
   - 쓰기: `PlayMotionSequence` action으로 모션 ID 1개(1~50) 재생.
   - 직접 관절 1 kHz 스트리밍, raw PDO/SDO, `{target position, feed-forward torque, Kp, Kd}` 레시피는 문서에서 참가자 비공개로 명시된다.
   - 따라서 카메라 목표 pose가 계속 변하는 온라인 서보 제어를 현재 공개 API만으로 구현할 수 있는지는 `REQUIRES_ORGANIZER_CONFIRMATION`이다.

3. **phact Studio와 phorce Studio는 서로 다른 층의 도구다.**
   - phact Studio: Web 기반 개별 phact 설정/검증 도구. 센서, 회전 방향·원점·정류, System ID, 제어 모드를 다룬다고 카탈로그에만 설명되어 있다. 실행 주소, 연결법, 파라미터, 저장 절차는 `NOT_FOUND_IN_REPOSITORY`이다.
   - phorce Studio: Windows 실행파일이 제공된 로봇 시스템 사전설정/직접교시 도구. 노트북–PCM USB 연결, 축 구성/이름/영점/부팅·종료 자세 저장, 1 kHz 직접교시 녹화, SD 모션 슬롯 저장, 재생 시험, 위치 PID 게인 모니터링을 한다.

4. **토크·임피던스·접촉 기능의 제품 존재와 참가자 구현 가능성은 구분해야 한다.**
   - phact-401 제품은 AFC, 임피던스 보상기, 모델 기반 토크 추정기, 2.5 kHz 전류 제어기, 위치·속도·토크 제한 기능을 가진다고 카탈로그에 적혀 있다.
   - 그러나 토크 모드 명령 API, 임피던스 식/파라미터, 전류–토크 상수, 접촉 판정 임계값, 제어 주기와 안전 한계는 저장소에 없다.
   - `/phorce/feedback`의 `current_a`와 `dob_a`는 관측 가능하지만, 이것만으로 검증된 접촉 감지기를 만들 수 있다는 근거는 없다.

5. **가장 먼저 할 일은 코딩이 아니라 6축 실물 식별 및 공개 제어 경로 확인이다.**
   - phorce Studio에서 실제 축 구성/이름/방향/영점과 슬롯을 읽고 기록한다.
   - Jetson에서 `phorce doctor`, 토픽/액션/타입 목록과 실제 `phorce list`를 캡처한다.
   - 운영진에게 연속 목표 pose/토크/임피던스 제어를 허용하는 참가자 API 또는 모션 슬롯 생성·갱신 경로가 있는지 확인한다.

## 1. 저장소 인벤토리

### 1.1 구조 및 파일 수

실제 조사 대상은 최상위 `idea1`과 `roboticus/` 아래 29개 파일, 총 30개다. `.git`, `.agents`, `.codex`는 비어 있으며 이 디렉터리는 유효한 Git 저장소가 아니다.

| 분류 | 수 | 비고 |
|---|---:|---|
| 텍스트/HTML/Markdown | 8 | `idea1`, HTML 6, MD 1 |
| PDF | 10 | 매뉴얼 5, 제품 2, 논문 3, OT 1 중 중복 표현 포함 |
| 실행/압축 | 2 | Windows EXE 1, 동일 EXE를 담은 ZIP 1 |
| 3D/2D 형상 | 5 | STL 4, DXF 1; STEP/3MF 없음 |
| 이미지 | 2 | 손그림 1, 콘셉트 렌더 1; 실물 조립 사진 없음 |
| 프레젠테이션 | 1 | PPTX 1, 내부 MP4 1 포함 |
| 메타데이터 | 2 | `.DS_Store` 2 |

### 1.2 없는 자료

- ROS 2 workspace/source, Python/C++ 소스, 메시지 정의: `NOT_FOUND_IN_REPOSITORY`
- SDK 설치 패키지 또는 Jetson 이미지: `NOT_FOUND_IN_REPOSITORY`
- URDF/SDF/MJCF, joint limit YAML, calibration 파일: `NOT_FOUND_IN_REPOSITORY`
- STEP, 3MF, Bambu Studio 프로젝트/슬라이싱 프로파일/G-code: `NOT_FOUND_IN_REPOSITORY`
- 실제 조립 사진, 치수 측정표, BOM, 링크 질량/재료/인필: `NOT_FOUND_IN_REPOSITORY`
- 클램프와 스마트폰 홀더 형상: `NOT_FOUND_IN_REPOSITORY`
- C270/스마트폰/iPad UI·스트리밍·카메라 제어 코드: `NOT_FOUND_IN_REPOSITORY`
- 이전 phact 실물 테스트 로그, EtherCAT 로그, 모션 CSV, 촬영 테스트 영상: `NOT_FOUND_IN_REPOSITORY`
- 빌드/실행 스크립트: `NOT_FOUND_IN_REPOSITORY`

## 2. 확인된 시스템과 제어 계약

### 2.1 통신 구조

```text
phorce Studio가 설치된 Windows 노트북
        │ USB
        ▼
PCM ── 내부선/FDCAN로 추정 ── phact-401 × 실제 구성 수
        ▲
        │ EtherCAT, NIC eno1, 1 kHz
        ▼
Jetson AGX Orin / ROS 2 / phorce gateway
```

- phact-401 자체 통신 방식은 카탈로그에서 **FDCAN**으로 명시된다.
- phorce Studio 매뉴얼은 PCM–phact 연결을 “내부선”이라고만 부른다. 이 시스템에서 실제로 FDCAN을 어떻게 배선/주소화하는지는 `NOT_FOUND_IN_REPOSITORY`이다.
- Jetson–PCM은 EtherCAT이다. 실물 스택 운영 예시는 `phorce_monitor --ros-args -p nic:=eno1 -p mode:=command -p axes:=2`와 `motion_action_server ... backend:=ecat`이다. 여기서 `axes:=2`는 런북의 벤치 예시이지 본 로봇의 6축 설정값이 아니다.
- 일반 참가자 문서는 최대 12축 시스템을 기준으로 메시지 배열을 설명한다. 실제 로봇은 phorce Studio에서 연결된 축 수를 저장해야 한다.

### 2.2 Jetson/사용자 프로그램에서 가능한 명령

#### CLI

| 명령 | 역할 |
|---|---|
| `phorce doctor` | 게이트웨이·카탈로그·상태 진단 |
| `phorce list` | PCM에 실제 적재된 모션 슬롯 조회 |
| `phorce play <id>` | 모션 ID 1개 재생, 완료까지 대기 |
| `phorce status` | 모션 슬롯 상태 읽기 |

- 공통 target: 실물 `robot` 또는 `sim:SESSION`.
- ID 범위 1~50, 0은 sentinel, 요청당 시퀀스 길이는 1, 큐가 없다.
- `BUSY`(코드 5)만 재시도 대상이다. 코드 12/13은 사람의 버튼 조작이 필요하다.

#### Python

확인된 공개 파사드:

```python
import phorce

with phorce.connect() as robot:
    result = robot.play(1)       # blocking
    handle = robot.play_async(2) # asynchronous
```

확인된 예외: `PhorceUnavailable`, `MotionBusy`, `MotionRejected`, `MotionAborted`.

#### C++

- 라이브러리: `phorce_cpp::motion_client`
- 생성: `MotionClient::attach(node, Target)`
- 요청: `play_async(id)` → `PlayOperation`
- 호출자가 ROS executor를 돌려야 하며 콜백에서 future를 블로킹하면 안 된다.

#### ROS 2

| 이름 | 타입 | 주기/QoS | 의미 |
|---|---|---|---|
| `/phorce/feedback` | `agx_msgs/msg/PhorceFeedback` | 1 kHz, sensor_data/best-effort | 12축 상태 |
| `/phorce/status` | `PhorceStatus` | 10 Hz, reliable | 모드·지터·카운터 |
| `/phorce/motion_window` | `MotionWindowStatus` | 2 Hz, latched | 슬롯 비트맵·busy |
| `/motion_action_server/play_motion_sequence` | `PlayMotionSequence` action | 이벤트 | 참가자 유일 구동 API |
| `.../motion_slot_state` | `MotionSlotState` | 문서 미기재 | 읽기 전용 |
| `~/list_motion_slots` | `ListMotionSlots` service | 이벤트 | 카탈로그 조회 |

`/phorce/feedback`는 반드시 `qos_profile_sensor_data`로 구독해야 한다. 축 값은 `axis[i].valid == true`일 때만 신뢰한다.

축별 확인 필드: `position_rad`, `velocity_rad_s`, `current_a`, `dob_a`, `bus_v`, `temp_c`, `kp_echo`, `kd_echo`, `valid`, `oper`, `stale`, `fault`.

`kp_echo` 단위는 A/rad, `kd_echo`는 A/(rad·s)로 문서에 적혀 있어 공개 피드백과 내부 레시피가 전류 도메인임을 보여 준다. 이를 Nm 기반 토크/강성으로 바꾸는 상수는 `NOT_FOUND_IN_REPOSITORY`이다.

### 2.3 안전 상태와 물리 버튼

- 파랑: 부팅/준비 중, 초록: 파킹·서보 해제, 노랑: 움직일 수 있음, 흰색: 종료 중, 빨강: 오류/E-stop.
- 기능 버튼 1: 초록 상태에서 약 1초 누름 → 3초 경고 후 서보 활성 및 부팅 자세 이동.
- 기능 버튼 2: 운전 중 약 1초 누름 → 정지·종료 자세·종료.
- E-stop: 모터 전원을 차단하며 해제 후에도 전원 재투입이 필요하다.
- 퀵스타트의 “버튼 1을 0.6초 이상”과 PCM 매뉴얼의 “1초” 표기가 다르다. 실무상 1초를 사용하되 정확한 debounce 임계값은 `NEEDS_VERIFICATION`이다.
- 소프트웨어 `cancel()`이나 “재생 정지”는 E-stop이 아니다.
- 문서는 게이트웨이가 하행 명령에 하드 veto→신선도→NaN→한계→slew 안전 감시를 적용한다고 설명하지만, 각 한계/수치는 `NOT_FOUND_IN_REPOSITORY`이다.

## 3. phact Studio와 phorce Studio

### 3.1 phact Studio

카탈로그에서 확인되는 범위:

1. Devices: Web에 연결된 phact 인식 및 연결 로그
2. Sensors: 내장 센서 확인과 파라미터 설정
3. Coordination: 구동 방향, 원점, 모터 정류 설정
4. System ID: 마찰과 응답 특성으로 물리 상수 식별
5. Control Mode: 제어 모드 선택, 안전 코드와 사용 시나리오 구성

다음은 모두 `NOT_FOUND_IN_REPOSITORY`다.

- 접속 URL/로컬 서버, 지원 OS·브라우저, USB/CAN 어댑터
- 축 ID 설정과 다축 네트워크 절차
- 제공되는 정확한 제어 모드 목록과 명령 구조
- System ID 시험 자세·하중·안전 조건과 결과 파라미터
- 토크 상수, 감속비, 방향 부호, 한계값, firmware/API 문서
- 설정의 임시/영구 저장 방식

따라서 phact Studio를 실제로 사용하기 전 운영진 자료가 필요하다: `REQUIRES_ORGANIZER_CONFIRMATION`.

### 3.2 phorce Studio

제공 파일은 Windows x86-64 PyInstaller one-file GUI다. ZIP 내부 EXE와 독립 EXE의 SHA-256은 동일하다.

권장 순서:

1. PCM이 초록(파킹/서보 해제)인지 확인한다.
2. Windows 노트북과 PCM을 USB로 연결하고 포트를 선택한다.
3. **① 설정**에서 로봇 이름, 실제 축 구성, 축 이름을 저장한다.
4. 실제 기준 자세에서 영점을 먼저 설정한다.
5. 부팅 자세, 종료 자세, 모션 오디오를 저장한다.
6. **② 교시**에서 빈 SD 슬롯 선택 → 서보 OFF → 1 kHz로 손 교시 녹화 → 그래프 화면 재생 → SD 카드 저장/검증 → 서보 ON 후 실물 재생 시험 → 서보 OFF.
7. **③ 모니터**에서 실시간 값/그래프/고속 로그를 보고 위치 PID 게인을 임시 적용한다. 검증된 게인만 phact 내부 메모리에 영구 저장한다.

설정은 PCM FLASH, 모션은 SD 카드, 영구 게인은 phact 내부 메모리에 남는다. “화면 재생”은 로봇을 움직이지 않고, ⑤의 “로봇에서 재생”만 실물을 움직인다.

phorce Studio는 런타임 카메라 pose 명령 도구가 아니라 **사전 설정과 모션 슬롯 제작 도구**다.

## 4. 토크·임피던스·접촉 감지·직접교시

### 4.1 토크 제어

확인됨:

- phact-401 순간최대/연속 토크: 27/7.2 Nm.
- 최대 속도: 150 rpm, 질량 0.51 kg, 크기 약 Ø85×40 mm.
- 연속 BLDC 출력 전류 최대 10 A.
- AFC, 모델 기반 토크 추정기, 고대역 전류제어기(2.5 kHz 대역폭), 동작 제한 알고리즘이 제품 기능으로 기재됨.

확인되지 않음:

- Jetson에서 torque setpoint를 보내는 API: `REQUIRES_ORGANIZER_CONFIRMATION`
- Nm/A, gear ratio, 효율, 포화/thermal derating: `NOT_FOUND_IN_REPOSITORY`
- torque loop 주기와 명령 watchdog: `NOT_FOUND_IN_REPOSITORY`
- 27 Nm를 허용하는 시간과 duty cycle: `NOT_FOUND_IN_REPOSITORY`

### 4.2 임피던스 제어

제품의 “임피던스 보상기”는 구동기 자신의 관성과 마찰을 상쇄해 명령 힘을 전달하는 내부 기능으로 설명된다. 이는 사용자가 원하는 Cartesian/joint impedance controller의 공개 API를 의미하지 않는다.

내부/벤치 레시피로 `{target position, feed-forward torque, Kp, Kd}`가 존재하지만 참가자 API가 아니라고 명시된다. 따라서 목표 강성·감쇠를 실시간 설정하는 방법은 `REQUIRES_ORGANIZER_CONFIRMATION`이다.

### 4.3 접촉 감지

가능한 관측 신호는 `current_a`, `dob_a`, `velocity_rad_s`, `position_rad`다. 그러나 다음이 없다.

- `dob_a`의 필터/부호/지연/신뢰 범위
- 전류·외란을 관절 토크로 환산하는 상수
- 중력/관성/마찰 보상 후 잔차 계산법
- 접촉 임계값, debounce, false-positive 검증 데이터

따라서 접촉 감지는 현재 상태에서 `REQUIRES_HARDWARE_TEST`이며, 운영진이 승인한 정적·저속 벤치에서 축별 baseline/no-contact/contact 로그를 먼저 수집해야 한다. 사진 로봇의 정상 운전에는 의도적 접촉이 필요하지 않으므로, 초기 시연은 “비정상 외력 감지 후 정지/복구”로 범위를 좁히는 편이 현재 API와 맞는다. 이 기능도 임계값을 정하기 전에는 구현 가능 판정을 내릴 수 없다.

### 4.4 직접교시

직접교시는 phorce Studio에서 확인된 기능이다.

- PCM 초록 상태, 서보 OFF에서 수행.
- 손으로 천천히 이동하며 PCM이 관절 각도를 1 kHz로 기록.
- 녹화 결과를 화면에서 확인한 뒤 SD 카드의 모션 슬롯에 저장.
- 저장 후 다시 읽어 검증하고 서보 ON 상태에서 실물 재생 시험.
- 영점을 먼저 정해야 하며 영점을 나중에 바꾸면 기존 모션이 어긋난다.

손 교시 중 AFC/중력보상/토크 모드가 어떻게 동작하는지는 `NOT_FOUND_IN_REPOSITORY`이다. “서보 OFF로 자유 이동”만 확인된다.

## 5. 기구 분석

### 5.1 형상 파일의 정량 정보

STL 단위는 파일 자체에 명시되지 않지만 phact 도면과 치수가 일치하므로 mm로 해석했다(`NEEDS_VERIFICATION`).

| 파일 | 메시 bounding box (mm) | 관찰 |
|---|---:|---|
| `NSK_6807ZZ.stl` | 7 × 47 × 47 | 지급 베어링 외형과 일치 |
| `phact-401.stl` | 85 × 40 × 85 | 제품 Ø85×40과 일치 |
| `joints.stl` | 332 × 268.83 × 452 | 조립 중립 자세; 150 disconnected components |
| `Robot_Body_Adapter.stl` | 298.95 × 144.75 × 407.10 | 디스플레이/몸체 프레임과 별도 원형 어댑터로 보임 |
| `GSHOCK_Platform.dxf` | 450 × 450 | 닫힌 사각형, Ø4 원 1,936개, 10 mm 격자 |

모든 STL은 조립/출력용으로 여러 분리 쉘과 비-manifold edge를 포함한다. 따라서 메시 부피를 곧바로 질량으로 환산하지 않았다.

### 5.2 `joints.stl`에서 식별되는 관절

phact 형상과 같은 대형 컴포넌트의 중심/두께 방향으로부터 얻은 **메시 기반 추정**:

| 추정 축 | 중심 (x,y,z) mm | 두께 방향→추정 회전축 | 다음 중심까지 거리 |
|---|---:|---|---:|
| A1 | (0, 0, 9) | Z | 약 121.3 mm |
| A2 | (0, 17.5, 129) | Y | 148 mm |
| A3 | (0, 17.5, 277) | Y | 108 mm |
| A4 | (0, 17.5, 385) | Y | 약 110.8 mm |
| A5 | (-108, 0, 367.5) | Z | 말단 |

따라서 이 STL의 중립 자세 추정 축 배열은 `Z–Y–Y–Y–Z`다. 이는 형상에서 추론한 것이며 축 양의 방향, zero, hard stop은 알 수 없다: `REQUIRES_HARDWARE_TEST`.

중심 간 총 경로는 약 488 mm지만 shoulder(A2)에서 A5까지 직선/체인 reach는 자세에 따라 달라진다. 원본 조립 구속과 링크 joint frame이 없으므로 정확한 DH/POE 모델은 만들 수 없다.

### 5.3 5축/6축 불일치

- OT: phact 6개 지급.
- 콘셉트 렌더: J1 base rotation, J2 shoulder, J3 elbow, J4 phone rotation, J5 phone tilt, J6 phone roll.
- `joints.stl`: phact 중심 5개 식별.
- 스마트폰 홀더/6번째 phact 형상: 없음.

가능한 해석은 6번째 축/holder가 아직 STL에 합쳐지지 않았거나, 메시 구성 해석에서 하나가 다른 부품에 포함됐거나, 실제 제작물이 CAD와 달라진 경우다. 어느 것도 저장소만으로 선택할 수 없다: `NEEDS_VERIFICATION`.

### 5.4 정적 토크 스크리닝

실제 정적 토크 계산에는 링크별 질량/CoM, 스마트폰+홀더 질량/CoM, 관절축, 자세가 필요하며 저장소에 없다. 따라서 아래는 설계값이 아니라 **phact 자체 질량만 이용한 최악 수평 자세 하한 스크리닝**이다.

- phact 질량 `m = 0.51 kg`, `g = 9.81 m/s²`.
- A2에서 원거리 세 phact가 대략 0.148, 0.256, 0.367 m에 있다고 놓으면:
  - `τ_A2, actuator-only ≈ 0.51×9.81×(0.148+0.256+0.367) ≈ 3.86 Nm`
- A3에서 원거리 두 phact를 약 0.108, 0.219 m로 놓으면:
  - `τ_A3, actuator-only ≈ 1.64 Nm`
- 이는 링크, 베어링, 볼트, 케이블, 스마트폰, 홀더, 누락된 6번째 phact를 모두 제외한 값이다.

A2는 actuator 자체만으로 연속 7.2 Nm의 약 54%를 쓸 수 있다. 누락된 질량과 동적 가속을 포함한 실제 margin은 `REQUIRES_HARDWARE_TEST`다. 순간 27 Nm를 정적 설계 용량으로 사용해서는 안 된다. 제조사 안전계수/thermal derating은 `REQUIRES_ORGANIZER_CONFIRMATION`이다.

### 5.5 workspace와 촬영 적합성

현재 저장소로 확인 가능한 사실:

- `joints.stl` 중립 조립 전체 높이는 약 452 mm.
- base yaw와 평행한 pitch 축 3개, 말단 추정 roll 축 1개가 있다.
- STL base는 클램프가 아니라 방사형 네 발 구조다.
- 스마트폰 렌즈 위치/광축/holder transform은 없다.

따라서 전신/상반신/배경 구도에 필요한 실제 camera workspace, 6D orientation coverage, singularity, joint limit, self-collision, 테이블 충돌은 `REQUIRES_HARDWARE_TEST`다. 특히 카메라 높이는 테이블 높이와 설치 transform이 없으므로 판단할 수 없다.

구조적으로 의심되는 항목:

- 평행 pitch 축 3개는 위치 reach를 만들지만 pitch 방향 기구 중복과 접힘 self-collision 가능성이 있다.
- 5축만 존재한다면 일반적인 6D end-effector pose를 독립적으로 지정할 수 없다. 촬영은 roll 또는 일부 position/orientation 자유도를 구도 제약으로 고정해 해결할 수 있지만 실제 5/6축 확인이 먼저다.
- base가 테이블 가장자리에서 멀수록 수평 하중이 클램프에 큰 전도 모멘트를 준다. 클램프 재질/접촉폭/허용 모멘트가 없다.
- 케이블 서비스 루프, strain relief, 스마트폰 낙하 방지 tether가 형상에 없다.

## 6. 목표 촬영 시나리오 판정

| 단계 | 판정 | 근거/누락 |
|---|---|---|
| 1. 사용자 접근 | 추가 코드 필요 | C270 입력/검출 코드 없음 |
| 2. 사람 수·위치·포즈·배경 인식 | 추가 코드 필요 | 카메라 제공 사실만 확인; 모델/성능/Jetson 파이프라인 없음 |
| 3. iPad Air 촬영 모드 선택 | 추가 코드 필요 | UI/네트워크 코드 없음 |
| 4. 현재 프레임 구도 평가 | 추가 코드 필요 | 평가 함수/데이터 없음 |
| 5. 목표 스마트폰 camera pose 계산 | 추가 코드+캘리브레이션 필요 | camera intrinsics/extrinsics, kinematics 없음 |
| 6. 관절 한계/충돌 검사 | 자료 부족으로 검증 불가 | URDF, limits, collision mesh 분리/frames 없음 |
| 7. 로봇팔 pose 조정 | 공개 API로는 연속 pose 제어 불가 | 저장 슬롯 재생만 확인; 동적 목표 대응은 `REQUIRES_ORGANIZER_CONFIRMATION` |
| 8. iPad 실제 프리뷰 | 추가 코드/기기 연동 필요 | 스마트폰→iPad 스트리밍 방식 없음 |
| 9. 카운트다운 | 바로 구현 가능한 일반 UI 기능 | 저장소 구현은 없음 |
| 10. 스마트폰 후면 촬영 | 추가 코드/기기 연동 필요 | 원격 shutter/API/OS 미정 |
| 11. 결과 표시 | 추가 코드/기기 연동 필요 | 전송/저장 형식 없음 |
| 12. 재촬영/저장 | 추가 코드/기기 연동 필요 | UI/파일 흐름 없음 |

현재 공개 제어 구조에 가장 잘 맞는 MVP는 continuous tracking이 아니라 **검증된 여러 camera pose를 직접교시해 슬롯으로 저장하고, 인식 결과에 따라 가장 가까운 슬롯 하나를 선택**하는 방식이다. 다만 모션 슬롯은 한 번에 하나만 재생되고 온라인 새 pose 생성 API는 없으므로 사용자 키/위치의 연속 변화에는 거친 양자화만 가능하다.

## 7. 논문과 교육 자료의 프로젝트 적용성

### 7.1 `ASAP: Aligning Simulation and Real-World Physics...`

- 핵심: 실물 rollout으로 delta action model을 학습해 시뮬레이터–실물 dynamics mismatch를 줄이고 정책을 fine-tune.
- 입력/출력: Unitree G1 23 DoF position target 정책과 PD controller, MoCap 기반 실물 trajectory.
- 본 프로젝트 적용: 디지털 트윈과 실물 궤적 오차를 수집할 수 있을 때 residual 보정 아이디어는 관련 있음.
- 즉시 적용 불가 이유: 연속 action API, 시뮬레이터 모델, MoCap, 대량 실물 rollout이 없음. 논문 자체도 과열/파손과 데이터 요구량을 한계로 든다.
- 판정: `Future Work`; 현재 100시간 MVP의 직접 제어 근거로 쓰기에는 `NOT_FOUND_IN_REPOSITORY` 항목이 많다.

### 7.2 `DREAM-Chunk: Reactive Action Chunking...`

- 핵심: 여러 action chunk와 latent future를 샘플링하고 관측과 가장 맞는 chunk로 실행 중 전환.
- 성립 조건: stochastic action policy, offline demonstration 50~100회 수준, 학습된 latent world model, high-rate action executor, corrective demonstrations.
- 본 프로젝트 적용: 프리셋 구도/모션 후보 중 현재 영상과 일치하는 후보를 재선택하는 발표/미래 구조로 관련 있음.
- 즉시 적용 불가 이유: 현재 phorce 계약은 요청당 모션 ID 하나, 큐 없음, 실행 중 chunk switching API가 문서화되지 않음.
- 판정: `Simulation / Future Work`; 단순 모션 슬롯 선택과 DREAM-Chunk 구현을 혼동하면 안 됨.

### 7.3 `GaP: A Graph-as-Policy...`

- 핵심: perception/planning/control을 typed skill node graph로 구성하고 simulator rehearsal로 성공률/throughput 최적화.
- 본 프로젝트 적용: `detect people → choose composition → validate safety → play slot → verify frame → trigger shutter`라는 해석 가능한 상태/스킬 그래프에 가장 직접적으로 적용 가능.
- 제한: 논문 구현은 MORSL/Isaac/Franka 등 별도 인프라에 의존하고 산업 수준 신뢰도에 못 미친다고 명시한다.
- 판정: 소프트웨어 아키텍처와 시뮬레이션 평가 방법은 적용 가능; 논문의 기존 코드/skill library는 저장소에 없으므로 `NOT_FOUND_IN_REPOSITORY`.

### 7.4 P-Vector 교육 PPT

- 5차 다항식 단위 위치 궤적을 `[yd, Ltrajectory, s0, sd]`로 나타내고 `MotionMap.csv`에서 축별 motion data를 구성하는 교육 자료다.
- y0/yd는 output 축 degree, s0/sd는 무차원 가감속 파라미터로 설명된다.
- walking/sit-to-stand 12축 예시가 있으나 CSV 스키마 전체, 실행 SDK, 안전 범위는 없다.
- 참가자 매뉴얼은 P/F/I Vector 편집을 행사 전 phorce Studio의 몫이자 참가자 비공개로 분류한다.
- 내부 136.25초 MP4는 WalkON SUIT F1 시연 영상으로, 본 촬영 로봇 테스트 로그가 아니다.

## 8. 지금 바로 실행할 다음 단계

### P0 — 실물과 인터페이스를 확정하기 전에는 코드 시작 금지

1. **실물 증거 패키지 촬영** (`REQUIRES_HARDWARE_TEST`)
   - 전체 정면/측면/상면, 클램프, 각 joint 양면, 스마트폰 holder, 케이블 경로.
   - 각 축에 A1~A6 임시 라벨을 붙이고 phact serial/ID를 기록.
   - 링크 축간 거리, 스마트폰+holder 질량/CoM, 링크별 질량, 테이블 높이, clamp offset 측정.

2. **phorce Studio read-only inventory** (`REQUIRES_HARDWARE_TEST`)
   - 초록/서보 OFF에서 연결.
   - 실제 검출 축 수/순서/이름, 현재 영점, 부팅/종료 자세, SD 슬롯 목록을 캡처.
   - 먼저 저장 버튼을 누르지 말고 현재 설정을 기록. 기존 영점/모션을 덮어쓰지 않는다.

3. **축 방향과 기구학 식별** (`REQUIRES_HARDWARE_TEST`)
   - 서보 OFF에서 축 하나씩 작은 각도로 움직여 `position_rad` 부호와 실제 회전 방향을 기록.
   - hard stop까지 밀지 말고 안전한 소범위에서 수행.
   - axis index↔물리 joint↔phact ID 표를 만든다.

4. **운영진 질의** (`REQUIRES_ORGANIZER_CONFIRMATION`)
   - 6축 임의 target position/velocity/torque/Kp/Kd를 Jetson에서 보내는 승인 API가 있는가?
   - 모션 실행 중 stop/switch의 안전한 계약은 무엇인가?
   - phact Studio URL/연결 어댑터/제어모드 매뉴얼을 제공할 수 있는가?
   - phact-401 torque constant, gear ratio, allowed peak duration, thermal derating은 무엇인가?
   - PCM–phact FDCAN 배선/ID와 axis count 설정은 누가 수행해야 하는가?

5. **Jetson 비구동 진단 캡처** (`REQUIRES_HARDWARE_TEST`)
   - `uname -r`, `/sys/kernel/realtime`, `phorce doctor --json`, `phorce list --json`.
   - `ros2 topic info -v /phorce/feedback`, `ros2 interface show agx_msgs/msg/PhorceFeedback`.
   - `ros2 action info -t /motion_action_server/play_motion_sequence`, action definition.
   - 이 단계에서는 `phorce play`를 실행하지 않는다.

### P1 — 저속·무하중 안전 검증

6. E-stop, 버튼 1/2, LED/음성 상태를 무부하/넓은 공간에서 확인.
7. 직접교시로 매우 작은 단일축 모션을 빈 슬롯에 저장하고 저속 재생. 기존 슬롯을 덮어쓰지 않음.
8. `/phorce/feedback`의 valid/oper/fault/current/temp와 모션 전후 로그를 저장.
9. 6축 확인 후 실제 joint limits와 self/table collision 금지 영역을 보수적으로 측정.

### P2 — 촬영 workspace 검증

10. 스마트폰 대신 같은 질량의 dummy payload로 전신/상반신/커플용 목표 camera 위치 3~5개를 수동 배치.
11. 각 pose에서 관절각, current, clamp 변위, 케이블 여유, 최소 충돌 간격을 기록.
12. 연속 API가 없으면 이 pose들을 모션 슬롯으로 직접교시하고 프리셋 MVP로 범위를 고정.

### Go/No-Go 기준

- **Go**: 6축 매핑, 영점, joint limits, dummy payload 정적 유지, E-stop, 3개 이상 촬영 pose, 안전한 슬롯 호출이 모두 확인됨.
- **Conditional Go**: 5축이지만 필요한 구도 프리셋 3개를 충돌 없이 만들 수 있음. 발표에서 5축/프리셋 한계를 명시.
- **No-Go/구조 재검토**: 연속 토크가 부족하거나 clamp가 움직임, 필수 구도가 workspace 밖, 케이블/자기충돌 회피 불가, 승인된 하행 API가 없고 슬롯 프리셋으로도 미션 불가.

## 9. 파일별 조사 기록

### `idea1`

파일 유형: UTF-8 Markdown 성격의 확장자 없는 텍스트  
역할: 초기 프로젝트/해커톤 맥락과 AI 촬영 로봇 아이디어  
프로젝트 관련성: 높음  
주요 내용: Physical AI, 접촉/마찰/복구 지향, 촬영 자동화 가치, 평가 항목  
연관 파일: OT PDF, prototype 이미지  
실행 또는 열람 방법: 텍스트 편집기/Markdown viewer  
현재 하드웨어에 적용되는 부분: 아이디어와 평가 기준만 적용  
확인되지 않은 부분: 문서가 중간 템플릿에서 끝나며 구현/기구 근거 없음 (`NEEDS_VERIFICATION`)

### `roboticus/OT_해커톤시작_2026-08-05_최종본 (공유).pdf`

파일 유형: 16쪽 PDF  
역할: 공식 행사 OT  
프로젝트 관련성: 높음  
주요 내용: phact 6개, Jetson AGX Orin, 볼트/베어링/C270, 미션·평가·일정·IP  
연관 파일: `idea1`, phact 카탈로그  
실행 또는 열람 방법: PDF viewer  
현재 하드웨어에 적용되는 부분: 지급품 수량/규격의 공식 근거  
확인되지 않은 부분: 정확한 phact firmware/API/제어 교육 내용 없음

### `roboticus/hackathon 2/01-quickstart.html`

파일 유형: HTML  
역할: 10분 실물/시뮬레이터 시작 절차의 원본 표현  
프로젝트 관련성: 높음  
주요 내용: doctor→feedback→list→버튼 1→play, E-stop, `phorce-console`  
연관 파일: 같은 이름 PDF, tutorial/manual  
실행 또는 열람 방법: 웹 브라우저  
현재 하드웨어에 적용되는 부분: 초기 연결/슬롯 재생  
확인되지 않은 부분: 실제 장비의 현재 슬롯/axis 설정 (`REQUIRES_HARDWARE_TEST`)

### `roboticus/hackathon 2/01-quickstart.pdf`

파일 유형: 4쪽 PDF  
역할: quickstart의 배포/인쇄본  
프로젝트 관련성: 높음, HTML과 내용 중복  
주요 내용: 위 HTML과 동일한 운영 흐름  
연관 파일: `01-quickstart.html`  
실행 또는 열람 방법: PDF viewer  
현재 하드웨어에 적용되는 부분: 현장 체크리스트  
확인되지 않은 부분: 버튼 hold 0.6초 표기가 PCM 매뉴얼 1초와 불일치 (`NEEDS_VERIFICATION`)

### `roboticus/hackathon 2/02-tutorial.html`

파일 유형: HTML  
역할: Python/rclpy/C++ 사용 튜토리얼  
프로젝트 관련성: 매우 높음  
주요 내용: `phorce.connect`, feedback valid/QoS, 빠른 관측/느린 판단 분리, 예외 처리  
연관 파일: 같은 이름 PDF, `03-manual`  
실행 또는 열람 방법: 웹 브라우저  
현재 하드웨어에 적용되는 부분: Jetson 사용자 프로그램 구조  
확인되지 않은 부분: 언급된 SDK 예제 원본이 저장소에 없음 (`NOT_FOUND_IN_REPOSITORY`)

### `roboticus/hackathon 2/02-tutorial.pdf`

파일 유형: 5쪽 PDF  
역할: tutorial 배포/인쇄본  
프로젝트 관련성: 매우 높음, HTML과 내용 중복  
주요 내용: Python/C++ 예제와 ROS QoS  
연관 파일: `02-tutorial.html`  
실행 또는 열람 방법: PDF viewer  
현재 하드웨어에 적용되는 부분: 현장 개발 참조  
확인되지 않은 부분: Jetson 설치 상태 (`REQUIRES_HARDWARE_TEST`)

### `roboticus/hackathon 2/03-manual.html`

파일 유형: HTML  
역할: 참가자 API/ROS/안전 계약 원본 표현  
프로젝트 관련성: 최상  
주요 내용: CLI/Python/C++/ROS 2, 슬롯 계약, reject code, 비공개 저수준 API  
연관 파일: 같은 이름 PDF, tutorial  
실행 또는 열람 방법: 웹 브라우저  
현재 하드웨어에 적용되는 부분: 구현 가능 범위의 기준  
확인되지 않은 부분: 실제 `.msg/.action` 정의와 gateway 소스 없음

### `roboticus/hackathon 2/03-manual.pdf`

파일 유형: 6쪽 PDF  
역할: manual 배포/인쇄본  
프로젝트 관련성: 최상, HTML과 내용 중복  
주요 내용: `03-manual.html`과 동일  
연관 파일: `03-manual.html`  
실행 또는 열람 방법: PDF viewer  
현재 하드웨어에 적용되는 부분: 현장 API 참조표  
확인되지 않은 부분: 저수준 torque/impedance API (`REQUIRES_ORGANIZER_CONFIRMATION`)

### `roboticus/hackathon 2/pcm-board-guide.html`

파일 유형: HTML  
역할: PCM LED/버튼/전원/복구 가이드 원본 표현  
프로젝트 관련성: 매우 높음  
주요 내용: 상태색, 버튼 1/2, E-stop latch, startup/shutdown, SD 주의  
연관 파일: 같은 이름 PDF, phorce Studio 매뉴얼  
실행 또는 열람 방법: 웹 브라우저  
현재 하드웨어에 적용되는 부분: 안전 운영  
확인되지 않은 부분: 실제 PCM 버전/firmware와 문서 일치 (`REQUIRES_HARDWARE_TEST`)

### `roboticus/hackathon 2/pcm-board-guide.pdf`

파일 유형: 5쪽 PDF  
역할: PCM 가이드 배포/인쇄본  
프로젝트 관련성: 매우 높음, HTML과 내용 중복  
주요 내용: 위 HTML과 동일  
연관 파일: `pcm-board-guide.html`  
실행 또는 열람 방법: PDF viewer  
현재 하드웨어에 적용되는 부분: 현장 안전 체크리스트  
확인되지 않은 부분: 실제 LED/error audio 기록 없음

### `roboticus/hackathon 2/phorce-studio-hackathon-manual.html`

파일 유형: HTML  
역할: phorce Studio 전체 workflow 원본 표현  
프로젝트 관련성: 최상  
주요 내용: USB 연결, 설정→교시→모니터, PCM/SD/phact 저장 위치, PID 적용/저장  
연관 파일: PDF, EXE, PCM guide  
실행 또는 열람 방법: 웹 브라우저  
현재 하드웨어에 적용되는 부분: 축 식별·영점·직접교시  
확인되지 않은 부분: 정확한 게인 단위/범위와 firmware 호환성

### `roboticus/hackathon 2/phorce-studio-hackathon-manual.pdf`

파일 유형: 10쪽 PDF  
역할: phorce Studio 매뉴얼 배포/인쇄본  
프로젝트 관련성: 최상, HTML과 내용 중복  
주요 내용: 위 HTML과 동일  
연관 파일: HTML, EXE  
실행 또는 열람 방법: PDF viewer  
현재 하드웨어에 적용되는 부분: 현장 순서표  
확인되지 않은 부분: manual의 참가자 사용 표현과 `03-manual`의 “행사 전/참가자 미사용” 표현이 충돌 (`NEEDS_VERIFICATION`)

### `roboticus/hackathon 2/phorce-studio.exe`

파일 유형: Windows x86-64 PyInstaller one-file GUI, 74,800,846 bytes  
역할: phorce Studio 실행 프로그램  
프로젝트 관련성: 최상  
주요 내용: 바이너리라 소스/API 검토 불가; SHA-256 `d61e3f8579684f8002fbb26cd93a39b6bdfba4042f4423c536e16ad0e93fc6d1`  
연관 파일: Studio manual, ZIP  
실행 또는 열람 방법: Windows에서 실행; Linux에서 직접 실행 불가  
현재 하드웨어에 적용되는 부분: PCM USB 설정/교시/모니터  
확인되지 않은 부분: 서명/version/지원 Windows/PCM firmware 호환성 (`NEEDS_VERIFICATION`)

### `roboticus/hackathon 2/phorce-studio-hackathon-20260804.zip`

파일 유형: ZIP  
역할: phorce Studio 배포 압축  
프로젝트 관련성: 높음, EXE와 중복  
주요 내용: 내부 파일은 `phorce-studio.exe` 하나이며 독립 EXE와 byte-identical  
연관 파일: `phorce-studio.exe`  
실행 또는 열람 방법: 압축 해제 후 Windows에서 실행  
현재 하드웨어에 적용되는 부분: 배포 편의  
확인되지 않은 부분: 추가 driver/installer가 없음 (`NEEDS_VERIFICATION`)

### `roboticus/hackathon 2/RT-FIX-10UNIT-ROLLOUT.md`

파일 유형: Markdown  
역할: Jetson 10대 RT kernel 복구/검수 운영 런북  
프로젝트 관련성: 높음  
주요 내용: RT kernel 판정, simulator smoke test, 실물 EtherCAT/motion server 시작 명령, 장애 대응  
연관 파일: HTML 버전, quickstart  
실행 또는 열람 방법: Markdown viewer/텍스트 편집기  
현재 하드웨어에 적용되는 부분: Jetson 이미지 검수와 운영진 실물 stack 기동  
확인되지 않은 부분: 참조된 fix script/inspection/HACKATHON-GUIDE가 저장소에 없음 (`NOT_FOUND_IN_REPOSITORY`)

### `roboticus/hackathon 2/RT-FIX-10UNIT-ROLLOUT.html`

파일 유형: HTML  
역할: 위 런북의 배포 표현  
프로젝트 관련성: 높음, MD와 내용 중복  
주요 내용: RT kernel/SDK/simulator/실물 stack 판정  
연관 파일: Markdown 버전  
실행 또는 열람 방법: 웹 브라우저  
현재 하드웨어에 적용되는 부분: 현장 운영 참고  
확인되지 않은 부분: 현재 팀 Jetson의 복구 완료 여부 (`REQUIRES_HARDWARE_TEST`)

### `roboticus/phact_info/phact_series_catalog_0729.pdf`

파일 유형: 4쪽 제품 카탈로그 PDF  
역할: phact 제품 기능/사양/라인업  
프로젝트 관련성: 최상  
주요 내용: phact-401 27/7.2 Nm, 150 rpm, 0.51 kg, FDCAN, AFC/임피던스/토크추정/2.5 kHz current controller  
연관 파일: phact 도면/STL  
실행 또는 열람 방법: PDF viewer  
현재 하드웨어에 적용되는 부분: 토크/질량/형상 1차 설계 근거  
확인되지 않은 부분: 상세 제어 API/상수/derating/안전계수

### `roboticus/phact_info/phact-401.pdf`

파일 유형: 1쪽 2D 기계 도면 PDF  
역할: phact-401 외형과 체결 치수  
프로젝트 관련성: 높음  
주요 내용: Ø85×40, PCD 80/78/38, M3/M4/M5와 깊이 표기  
연관 파일: `phact-401.stl`, 카탈로그  
실행 또는 열람 방법: PDF/CAD viewer  
현재 하드웨어에 적용되는 부분: 인터페이스 치수 검토  
확인되지 않은 부분: 출력축 방향 정의, 허용 radial/axial load, 체결 토크 (`NOT_FOUND_IN_REPOSITORY`)

### `roboticus/3d print/phact-401.stl`

파일 유형: binary STL  
역할: phact 외형 참조 메시  
프로젝트 관련성: 높음  
주요 내용: 약 85×40×85 mm, 51,879 triangles, 26 shells  
연관 파일: 2D 도면, `joints.stl`  
실행 또는 열람 방법: STL/CAD/slicer viewer  
현재 하드웨어에 적용되는 부분: envelope와 메시 내 phact 식별  
확인되지 않은 부분: 정확한 joint frame/질량 특성; 제조용 모델 여부

### `roboticus/3d print/NSK_6807ZZ.stl`

파일 유형: binary STL  
역할: 6807ZZ 베어링 외형 참조  
프로젝트 관련성: 중간  
주요 내용: 47×47×7 mm, 지급 규격과 일치  
연관 파일: OT PDF, joints  
실행 또는 열람 방법: STL/CAD/slicer viewer  
현재 하드웨어에 적용되는 부분: 베어링 envelope  
확인되지 않은 부분: 실제 제조사/하중 등급/fit tolerance (`NOT_FOUND_IN_REPOSITORY`)

### `roboticus/3d print/joints.stl`

파일 유형: binary STL assembly mesh  
역할: 관절/링크/베이스 중립 자세 조립 참고  
프로젝트 관련성: 최상  
주요 내용: 332×268.83×452 mm, 365,424 triangles, 150 shells, phact 중심 5곳  
연관 파일: phact/bearing STL, 콘셉트 렌더  
실행 또는 열람 방법: STL/CAD viewer; 조립 의미는 mesh inspection 필요  
현재 하드웨어에 적용되는 부분: 대략적 축 위치/링크 간격/베이스 형상  
확인되지 않은 부분: 6번째 축, 조립 구속, limits, 물성, 케이블, 실제 제작 revision (`NEEDS_VERIFICATION`)

### `roboticus/3d print/Robot_Body_Adapter.stl`

파일 유형: binary STL, 4 shells  
역할: 디스플레이/몸체 프레임과 원형 어댑터로 보이는 구조  
프로젝트 관련성: 중간  
주요 내용: 약 299×145×407 mm  
연관 파일: 콘셉트 렌더  
실행 또는 열람 방법: STL/CAD/slicer viewer  
현재 하드웨어에 적용되는 부분: 테이블 디스플레이 후보 형상  
확인되지 않은 부분: 어떤 iPad용인지, 조립 위치, 재료/인필/체결, 실제 출력 여부 (`NEEDS_VERIFICATION`)

### `roboticus/GSHOCK_Platform.dxf`

파일 유형: AutoCAD R14 DXF  
역할: 450 mm 정사각 타공 플랫폼  
프로젝트 관련성: 낮음~중간  
주요 내용: 450×450 외곽, Ø4 mm 원 1,936개가 10 mm 격자에 배치  
연관 파일: 없음  
실행 또는 열람 방법: 2D CAD/DXF viewer  
현재 하드웨어에 적용되는 부분: 사용 위치가 문서화되지 않음  
확인되지 않은 부분: 재료/두께/제조법/촬영 로봇과의 연결 (`NOT_FOUND_IN_REPOSITORY`)

### `roboticus/prototype/KakaoTalk_Photo_2026-08-06-11-53-16.jpeg`

파일 유형: 764×743 JPEG  
역할: 초기 손그림 콘셉트  
프로젝트 관련성: 중간  
주요 내용: 화면 몸체, 얼굴, 양팔, 스마트폰의 개념 배치  
연관 파일: `idea1`, 콘셉트 렌더  
실행 또는 열람 방법: 이미지 viewer  
현재 하드웨어에 적용되는 부분: 외형 아이디어만  
확인되지 않은 부분: 실제 치수/관절/제작 상태를 증명하지 않음

### `roboticus/prototype/KakaoTalk_Photo_2026-08-06-11-53-34.jpeg`

파일 유형: 1536×1024 JPEG  
역할: AI 콘셉트 보드/렌더  
프로젝트 관련성: 아이디어에는 높음, 실물 검증에는 낮음  
주요 내용: 이동형 6축 PhotoMate, 1450×650×600 mm/45 kg 등 콘셉트 사양, J1~J6 라벨  
연관 파일: 손그림, `joints.stl`  
실행 또는 열람 방법: 이미지 viewer  
현재 하드웨어에 적용되는 부분: 사용자 경험/발표 시각화 후보  
확인되지 않은 부분: 현재 고정형·클램프 스코프와 충돌하며 실물/CAD 근거가 아님; `AI Concept Visualization`로만 표시해야 함

### `roboticus/모터제어_p vector.pptx`

파일 유형: 5슬라이드 PPTX, 내부 136.25초 MP4 포함  
역할: P-Vector 위치 궤적 교육  
프로젝트 관련성: 중간  
주요 내용: 5차 다항식, yd/Ltrajectory/s0/sd, MotionMap.csv 예시, 12축 walking/sit-to-stand  
연관 파일: phorce manual/Studio  
실행 또는 열람 방법: PowerPoint/LibreOffice; 내부 영상은 일반 player  
현재 하드웨어에 적용되는 부분: 저장 모션의 내부 개념 이해  
확인되지 않은 부분: CSV 전체 계약과 participant edit/upload 경로 (`REQUIRES_ORGANIZER_CONFIRMATION`)

### `roboticus/논문/2502.01143v3.pdf`

파일 유형: 18쪽 논문 PDF  
역할: ASAP sim-to-real delta action 연구  
프로젝트 관련성: 중간/미래  
주요 내용: 실물 rollout 기반 dynamics mismatch 보정, G1 whole-body position target+PD  
연관 파일: OT의 공지 논문 조건  
실행 또는 열람 방법: PDF viewer  
현재 하드웨어에 적용되는 부분: digital twin residual calibration 개념  
확인되지 않은 부분: 본 로봇 simulator/action API/data pipeline 없음

### `roboticus/논문/2606.18589v1.pdf`

파일 유형: 16쪽 논문 PDF  
역할: DREAM-Chunk reactive action chunking 연구  
프로젝트 관련성: 중간/미래  
주요 내용: candidate chunk latent rollout/matching, corrective demonstrations, 실물 4 task  
연관 파일: 모션 슬롯/직접교시 개념  
실행 또는 열람 방법: PDF viewer  
현재 하드웨어에 적용되는 부분: 후보 촬영 모션의 반응형 재선택 아이디어  
확인되지 않은 부분: stochastic policy/world model/high-rate executor 없음

### `roboticus/논문/2607.05369v1.pdf`

파일 유형: 52쪽 논문 PDF  
역할: GaP variational automation/skill graph 연구  
프로젝트 관련성: 높음(아키텍처), 낮음(코드 재사용)  
주요 내용: typed perception/planning/control graph, simulation rehearsal, success/throughput  
연관 파일: 목표 촬영 시나리오  
실행 또는 열람 방법: PDF viewer  
현재 하드웨어에 적용되는 부분: 상태/스킬 그래프와 단계별 검증 구조  
확인되지 않은 부분: MORSL/GaP/Isaac 코드 및 모델은 저장소에 없음

### `roboticus/.DS_Store`

파일 유형: macOS Finder 메타데이터  
역할: 폴더 표시 설정  
프로젝트 관련성: 없음  
주요 내용: 프로젝트 기술 근거 없음  
연관 파일: 없음  
실행 또는 열람 방법: 일반적으로 열람 불필요  
현재 하드웨어에 적용되는 부분: 없음  
확인되지 않은 부분: 없음

### `roboticus/hackathon 2/.DS_Store`

파일 유형: macOS Finder 메타데이터  
역할: 폴더 표시 설정  
프로젝트 관련성: 없음  
주요 내용: 프로젝트 기술 근거 없음  
연관 파일: 없음  
실행 또는 열람 방법: 일반적으로 열람 불필요  
현재 하드웨어에 적용되는 부분: 없음  
확인되지 않은 부분: 없음

## 10. 발표 분류 제안

- `Physical Prototype`: 실물에서 실제 확인한 축 수/동작/촬영 pose만 포함.
- `Implemented Software`: Jetson/C270/iPad/스마트폰에서 실제 실행 및 측정한 기능만 포함.
- `Simulation / Digital Twin`: GaP식 상태 그래프나 workspace/충돌 시각화 중 실제 로봇과 calibration된 것만 포함.
- `AI Concept Visualization`: 현재 PhotoMate 렌더, 이동형 외형, 미구현 UI/완성 장면.
- `Future Work`: ASAP delta alignment, DREAM-Chunk, 연속 impedance/contact control, 이동 베이스.

현재 콘셉트 렌더의 이동 베이스, 45 kg, 1450 mm, 실외/실내, 6축 완성 외형은 저장소의 실물 증거가 아니므로 반드시 `AI Concept Visualization`로 표시해야 한다.
