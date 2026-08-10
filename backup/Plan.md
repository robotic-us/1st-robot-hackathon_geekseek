# RPI Plan — ONE_SHOT_UPPER_MID Vertical Slice

- 작성일: 2026-08-06 (Asia/Seoul)
- 기준 리서치: `RESEARCH_REPORT.md`, `RESEARCH_SESSION_2.md`
- 대상 저장소: <https://github.com/robotic-us/1st-robot-hackathon_geekseek.git>
- 현재 단계: **R/P만 수행**. 아래 시작 게이트를 통과하기 전에는 I(구현)를 시작하지 않는다.

## 0. 결론과 현재 RPI 상태

현재 저장소 자료로 수행할 수 있는 **문서·CAD·SDK 리서치는 첫 MVP의 방향을 정할 만큼 완료**됐다. 공개 API에서 맞는 구조는 온라인 IK나 임의 관절 제어가 아니라, phorce Studio로 실물 검증한 모션 슬롯 하나를 Jetson의 상태기계가 한 번 재생하고 실제 정지 후 촬영하는 구조다.

그러나 R 전체가 끝난 것은 아니다. 다음 항목은 문서만으로 확정할 수 없으며, 구현 전에 실물 또는 운영진 확인이 필요하다.

| ID | 남은 확인 | 완료 증거 | 미완료 시 영향 |
|---|---|---|---|
| R1 | PCM 실제 축 수와 ID↔A1~A5 매핑, sign, zero | phorce Studio 화면/기록표와 `phorce doctor/status` 로그 | 로봇 구동 구현 금지 |
| R2 | `UPPER_MID` 슬롯 ID, 시작 자세, 실행 시간 | `phorce list` 결과와 phorce Studio 저속 재생 영상/기록 | 실물 play 금지 |
| R3 | dummy phone 포함 holder 체결, 질량/CoM, base 고정, cable/joint limit | 체크리스트와 설치 사진 | payload 장착 재생 금지 |
| R4 | 사용할 폰, 렌즈, orientation, preview 및 shutter 명령 계약 | 한 번의 원격 촬영과 파일 저장 확인 | 실제 camera adapter 구현 보류 |
| R5 | A5→holder→camera 방향과 상반신 바닥 표식 | 캘리브레이션 버전과 샘플 프레임 | 구도 합격 판정 불가 |
| R6 | 허용 온도·전류 기준 | 제조사/운영진이 승인한 수치와 출처 | 소프트웨어가 임의 임계값을 만들지 않음; 사람이 감독 |
| R7 | 실제 개발 기준 Git checkout | `.git`과 `origin`이 대상 URL을 가리키고 clean baseline 기록 | 커밋/PR 작업 금지 |

따라서 R 판정은 **desk research 완료 / hardware research 미완료**다. R1~R6의 증거를 `docs/bringup/`에 남기고 R7의 Git baseline을 확인하면 첫 vertical slice에 필요한 R을 종료하고 I로 넘어간다.

## 1. 목표

고정된 한 명이 지정된 바닥 위치에 서 있고, 스마트폰 방향·렌즈·상반신 구도가 고정된 조건에서 다음 경로를 안전하게 1회 수행한다.

```text
manual start edge
  → preflight
  → UPPER_MID slot 1회 재생
  → action result 확인
  → physical_idle 및 5축 velocity settle 확인
  → frame 유효성 확인
  → shutter 1회
  → 저장 성공 표시
  → cooldown 후 재무장
```

AI가 관절값을 생성하지 않는다. 첫 버전의 “지능”은 검증된 skill을 안전한 시점에 선택·실행하고, 실패를 숨기지 않는 supervisor에 둔다.

### 완료 조건

- 같은 zero/slot/camera calibration에서 10회 연속 실행한다.
- 중복 motion request와 중복 shutter가 각각 0회다.
- 모든 실행 전후에 기대한 5개 축의 `valid && oper && !stale && !fault`를 확인한다.
- action 완료만으로 촬영하지 않고 `physical_idle`과 연속 velocity settle 조건을 모두 만족한다.
- 10장 모두 정의된 상반신 frame 영역 안에 있고 심한 motion blur가 없다.
- 사람/폰/베이스 충돌, holder 이동·풀림, 케이블 걸림이 0회다.
- BUSY 이외의 거절·abort·stale·fault·camera 실패는 자동 재실행하지 않고 명시적 오류 상태로 간다.
- 각 run의 상태 전이, slot, 축 상태, 온도/전류 관측값, shutter 결과를 로그로 남긴다.

## 2. 구현 범위

### 포함

1. 수동 시작 입력 하나의 rising edge 처리
2. 단일 preset `UPPER_MID` registry와 설정 검증
3. phorce preflight, 단일-flight play, 결과/오류 매핑
4. 12칸 feedback에서 `valid`인 실제 축을 찾는 관측기
5. 명시적 supervisor 상태기계
6. 연속 표본 기반 settle 판정과 cooldown/re-arm
7. 교체 가능한 frame validator와 camera shutter interface
8. mock 기반 자동 테스트, 시뮬레이션 실행, 실물 acceptance 기록

### 비범위 — 이번 I에서 바꾸지 않을 것

- CAD/STL, holder, base, 배선 및 phact/phorce firmware 수정
- phact 방향·영점·게인과 phorce Studio 슬롯을 코드에서 쓰거나 자동 변경
- raw PDO/SDO, `/phorce_monitor/arm`, `/phorce_monitor/confirm`, `/phorce/submit_motion` 호출
- arbitrary joint target, continuous IK/servoing, torque/impedance/contact controller
- 다중 preset, FULL shot, 키/인원 bin, 자동 preset 선택
- 사람 검출·추적·포즈 추천·학습 모델; 첫 frame validator는 수동 승인 또는 확정된 단순 adapter
- 렌즈 전환, digital zoom, autofocus/exposure 제어, 사진 보정
- iPad/모바일 완성 UI, 계정·클라우드 업로드·갤러리 서비스
- fault 이후 버튼 2/E-Stop/전원 재인가의 자동화
- 출처 없는 joint/current/temperature 안전 한계 추정
- SDK 제공 코드와 `analysis/session2/` 산출물 변경

## 3. 아키텍처와 상태 계약

순수한 상태기계와 실제 I/O adapter를 분리한다. 테스트는 로봇이나 ROS 2 없이 상태기계를 완전히 실행하고, Jetson에서는 adapter만 SDK와 연결한다.

```text
CLI manual start
      │
      ▼
Supervisor FSM ─── PresetRegistry / SafetyConfig
   │       │
   │       ├── PhorcePort ── phorce Python API + ROS 2 feedback/status
   │       └── CameraPort ── 확정된 preview/shutter 계약
   ▼
JSONL audit log
```

상태는 다음으로 고정한다.

```text
PARKED → PREFLIGHT → IDLE → EXECUTING → SETTLING
       → FRAME_VALIDATE → CAPTURE → COOLDOWN → IDLE

어디서든:
BUSY → IDLE(유한 대기 후 명시적 재시작만 허용)
reject 12/13 → OPERATOR_REQUIRED
abort/fault/stale/axis mismatch/timeout → FAULT
camera/frame 실패 → CAPTURE_FAILED
```

핵심 불변조건은 다음과 같다.

- `EXECUTING` 동안 두 번째 play를 보내지 않는다.
- start가 계속 참이어도 rising edge 하나당 run 하나만 만든다.
- `COMPLETED + physical_idle`도 idle로 인정한다.
- action feedback의 `current_motion_id=0`, `pvector_index=255`를 진행률로 사용하지 않는다.
- feedback callback은 최신 표본만 저장하고, 2~5 Hz supervisor가 판단한다.
- settle은 기대 축 전체가 승인된 velocity threshold 아래인 표본이 지정 시간 연속 관측될 때만 참이다. threshold와 시간은 설정에 출처와 버전을 기록한다.
- 프로세스 timeout/Ctrl+C/cancel을 물리 정지로 간주하지 않는다.

## 4. 만들 파일

구현은 Python 3 패키지로 시작한다. ROS 2/SDK import는 adapter 경계 안에만 둔다.

| 파일 | 역할 |
|---|---|
| `pyproject.toml` | 패키지, CLI entry point, pytest/ruff 설정 |
| `README.md` | 설치, mock 실행, Jetson 실행, 안전 경고, 복구 링크 |
| `config/presets.yaml` | `UPPER_MID` slot ID, required start pose, calibration/zero version, cooldown |
| `config/safety.yaml` | expected axis ID 집합, feedback freshness, settle 조건; 모든 실물 수치의 출처 기록 |
| `src/geekseek/__init__.py` | 패키지 버전 |
| `src/geekseek/domain.py` | 상태/이벤트/오류 enum과 preset/run dataclass |
| `src/geekseek/ports.py` | `PhorcePort`, `CameraPort`, `FrameValidator`, `Clock` protocol |
| `src/geekseek/config.py` | YAML 로딩과 fail-closed schema/교차 검증 |
| `src/geekseek/observer.py` | 12축 latest-value cache, expected valid-axis와 settle 판정 |
| `src/geekseek/supervisor.py` | 순수 상태기계, edge trigger, single-flight, cooldown |
| `src/geekseek/adapters/phorce_sdk.py` | 공식 phorce play/status/list와 ROS 2 sensor-data QoS feedback 연결 |
| `src/geekseek/adapters/camera.py` | R4에서 확정한 camera 계약의 최소 preview/shutter adapter |
| `src/geekseek/adapters/manual_frame.py` | 첫 실물 시험용 operator frame 승인 adapter |
| `src/geekseek/adapters/fakes.py` | 테스트/데모용 robot, camera, clock fake |
| `src/geekseek/logging.py` | run별 JSONL audit event 기록; 이미지 자체는 저장하지 않음 |
| `src/geekseek/cli.py` | `preflight`, `run-once`, `mock-run` 명령 |
| `tests/unit/test_config.py` | 잘못된 slot/축/버전/threshold 설정 거절 |
| `tests/unit/test_observer.py` | valid mask, stale/fault, 축 불일치, 연속 settle 조건 |
| `tests/unit/test_supervisor.py` | 모든 정상/실패 전이, edge/cooldown/single-flight 불변조건 |
| `tests/unit/test_error_policy.py` | BUSY/reject/abort/unavailable/camera 오류 정책 |
| `tests/integration/test_run_once_fake.py` | fake robot+camera로 단발 촬영 end-to-end |
| `tests/integration/test_no_duplicate_commands.py` | start 고정/반복 callback에서도 play/shutter 각 1회 검증 |
| `docs/bringup/hardware-inventory.md` | R1/R3/R6 결과와 실제 축 mapping |
| `docs/bringup/upper-mid-preset.md` | R2/R5 slot 교시·구도·clearance·payload 증거 |
| `docs/bringup/camera-contract.md` | R4 폰/렌즈/orientation/preview/shutter/save 계약 |
| `docs/bringup/acceptance-checklist.md` | E-Stop 담당자, 사전 점검, 10회 결과와 중단 기준 |
| `scripts/jetson_preflight.sh` | `doctor/list/status`, ROS 격리, package version을 읽기 전용으로 수집 |

`camera.py`의 구체 프로토콜은 R4가 결정되기 전 작성하지 않는다. 필요하면 파일명도 `android_camera.py`, `ios_camera.py`, `http_camera.py` 중 실제 계약에 맞게 바꾸며, 가상의 범용 API를 만들지 않는다.

## 5. 기존 파일에서 바꿀 것

| 파일 | 변경 |
|---|---|
| `README.md` | 새로 없으면 만들고, 있으면 기존 설명을 보존하면서 MVP 실행/안전/문서 링크 추가 |
| `.gitignore` | 저장소에 존재할 경우 기존 규칙을 보존하며 `.venv/`, cache, runtime log, 촬영 결과만 추가 |
| `RESEARCH_SESSION_2.md` | 내용은 수정하지 않고 Plan의 근거 문서로만 사용 |
| `RESEARCH_REPORT.md` | 내용은 수정하지 않고 Plan의 근거 문서로만 사용 |

실제 구현 직전 `git status`, tracked files, 기존 `README.md`/`pyproject.toml`을 다시 확인한다. 같은 파일이 원격 저장소에 이미 있으면 덮어쓰지 않고 현재 구조에 맞춰 최소 변경한다.

## 6. 구현 순서

### P0 — Repository와 Research gate

1. 대상 GitHub 저장소의 실제 checkout/branch/remote와 clean baseline을 확인한다.
2. R1~R6을 실물에서 확인하고 `docs/bringup/` 네 문서를 채운다.
3. slot, expected axes, camera contract, 승인된 안전 수치가 없으면 mock 구현까지만 허용한다.

종료 조건: R1~R7 증거가 있고 팀원이 slot ID, 축 집합, camera adapter 선택을 리뷰했다.

### P1 — Pure domain과 supervisor

1. domain/ports/config를 만든다.
2. 상태기계, edge trigger, single-flight, error policy를 구현한다.
3. fake clock/robot/camera로 모든 상태 전이를 단위 테스트한다.

종료 조건: 하드웨어 의존성 없이 정상 1회와 모든 실패 경로 테스트가 통과한다.

### P2 — Observer와 phorce adapter

1. `/phorce/feedback`을 `qos_profile_sensor_data`로 구독한다.
2. 12칸 중 expected `valid` 축만 사용하고 mask/oper/stale/fault/freshness를 검증한다.
3. 공식 SDK의 list/status/play만 연결하고 예외를 domain error로 변환한다.
4. `preflight`를 실물 구동 없이 먼저 실행한다.

종료 조건: 로봇을 움직이지 않고 실제 5축 health/idle/slot을 정확히 판정하고 로그로 남긴다.

### P3 — Camera adapter와 mock end-to-end

1. R4에서 확정한 shutter/save 응답만 최소 구현한다.
2. manual frame validator를 연결한다.
3. `mock-run`에서 play→settle→approve→shutter가 정확히 한 번씩 호출되는지 확인한다.

종료 조건: camera timeout/save failure를 포함한 integration test가 통과한다.

### P4 — 제한된 실물 bring-up

1. E-Stop 담당자 1명, 관찰자 1명, clear zone, dummy phone으로 시작한다.
2. 로봇 전원 → monitor(`mbx_enabled:=true`) → action server → 버튼 1 → 총 10초 → `physical_idle` 순서를 지킨다.
3. 처음에는 play 없이 preflight/feedback만 검증한다.
4. phorce Studio에서 이미 검증한 시작 자세에서 `run-once --no-shutter` 1회 실행한다.
5. 이상음/탄내/뜨거움/간섭/holder 이동이 없을 때만 shutter를 연결한다.

종료 조건: dummy payload 3회가 안전하고 audit log가 실제 관측과 일치한다.

### P5 — Acceptance와 demo freeze

1. 고정 조건에서 10회 acceptance를 수행한다.
2. 실패 사례와 operator recovery 화면을 함께 촬영한다.
3. 설정/zero/slot/camera calibration 버전을 고정하고 데모 이후 임의 변경하지 않는다.

종료 조건: 1장의 acceptance 기록에 완료 조건 전부가 체크되고 데모용 fallback 절차가 준비된다.

## 7. 테스트 계획

### 자동 테스트

```bash
python -m pytest -q
python -m ruff check .
```

필수 테스트 케이스:

- start `false→true` 한 번에 play 1회, shutter 1회
- start가 true로 유지되거나 callback이 폭주해도 추가 명령 0회
- cooldown 전 두 번째 start 무시, false로 re-arm 후에만 다음 run 허용
- expected axis 5개가 아닌 경우, 하나라도 invalid/stale/not-oper/fault인 경우 fail closed
- action result가 와도 velocity가 안정되지 않으면 CAPTURE로 가지 않음
- `COMPLETED + physical_idle`은 idle, `COMPLETED + !physical_idle`은 비-idle
- BUSY는 bounded wait 후 IDLE로 돌아가되 자동 play 연타 없음
- reject 12/13은 OPERATOR_REQUIRED, abort/unavailable/timeout은 FAULT
- frame reject와 camera 저장 실패에서 shutter 재시도/robot replay 없음
- 잘못된 slot 범위, 누락된 calibration version, 출처 없는 안전 설정 로드 실패

### 실물 테스트

실물 테스트는 자동화 테스트와 별도다. 매 run마다 다음을 기록한다.

```text
run_id / timestamp / operator
zero_version / slot_id / calibration_version
pre/post valid-axis set / physical_idle / settle duration
축별 max |velocity| / max temp / max current (관측값)
play request count / shutter count / image save result
framing / blur / collision / holder movement / cable issue
```

즉시 중단 조건: E-Stop 필요 상황, 사람/기구 간섭, holder 풀림, 이상음·탄내·과도한 열, 축 상태 상실, 실제 움직임과 소프트웨어 상태 불일치. 프로세스 종료로 로봇이 멈춘다고 가정하지 않는다.

## 8. 평가 항목과 시연 연결

| 기능 | 평가 항목 | 시연 장면 | 정량 지표 | 실패 시 대체 시연 |
|---|---|---|---|---|
| 검증된 촬영 slot 단발 실행 | 미션 달성, 기술 활용도 | 버튼 1회로 상반신 구도 이동 | 중복 play 0/10 | phorce Studio 검증 영상 + mock FSM |
| 실제 정지 후 shutter | 기술 활용도, 시연 | 움직임 종료 후 흔들림 없는 촬영 | blur 실패 0/10 | settle 로그와 저장된 샘플 사진 |
| fail-closed supervisor | 기술 활용도, 발표 | fault/frame reject 시 촬영 차단 | 잘못된 shutter 0회 | fake fault 주입 데모 |
| 반복 가능한 구도 | 창의성, 미션 달성 | 같은 위치에서 10장 연속 비교 | frame 합격 10/10 | calibration/acceptance 기록 |

## 9. I 시작 체크리스트

- [ ] 실제 Git checkout과 origin/branch 확인
- [ ] R1 실제 축 mapping/zero 기록
- [ ] R2 `UPPER_MID` slot 및 시작 자세 검증
- [ ] R3 base/holder/payload/cable 안전 확인
- [ ] R4 camera preview/shutter/save 계약 확정
- [ ] R5 camera 방향과 frame 기준 확정
- [ ] R6 온도·전류 정책을 운영진에게 확인
- [ ] config 값과 출처를 팀 리뷰
- [ ] E-Stop 담당자와 clear zone 확보
- [ ] 그 뒤 P1 구현 시작

이 체크리스트가 완료되기 전에도 P1의 순수 상태기계와 fake 테스트는 개발할 수 있지만, 실제 로봇 adapter를 통한 play와 실제 camera adapter 구현은 시작하지 않는다.
