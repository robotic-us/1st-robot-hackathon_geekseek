# RPI Research Session 2 — Existing 5-DoF Manipulator System Analysis

- 조사일: 2026-08-06 (Asia/Seoul)
- 기준 문서: `RESEARCH_REPORT.md`
- 범위: 현재 `joints.stl`에 들어 있는 5축 매니퓰레이터와 phact/phorce 제어 경로
- 제외: 애플리케이션 구현, CAD 수정, 실물 구동, 외부 웹 조사

## 판정 표기

- **메시 확인**: STL에서 직접 측정하거나 참조 STL과 형상 비교로 확인했다.
- **문서 확인**: 저장소의 phact/phorce 공식 제공 문서에 명시돼 있다.
- **기구 추정**: 메시와 일반적인 회전관절 기구학에 가장 잘 맞지만 조립 constraint나 실물 시험으로 확인하지 못했다.
- **확인 필요**: 저장소 자료만으로 결정할 수 없다.

## 0. 결론

1. `joints.stl`의 제작 대상은 **회전관절 5개와 고정 베이스로 이루어진 serial manipulator**다. phact 본체형 shell이 정확히 5개 검출되며, 중립 자세의 축 배열은 **`Z–Y–Y–Y–Z`**가 맞다. 단, 축의 양의 방향과 zero는 STL에서 알 수 없다.
2. 중심은 A1 `(0, 0, 9)`, A2 `(0, 17.5, 129)`, A3 `(0, 17.5, 277)`, A4 `(0, 17.5, 385)`, A5 `(-108, 0, 367.5)` mm다. 중심간 거리는 약 `121.27, 148, 108, 110.80 mm`다.
3. A1은 base yaw, A2~A4는 같은 평면의 shoulder/elbow/wrist pitch 체인, A5는 말단의 축방향 회전으로 해석하는 것이 형상과 일치한다. 그러나 **A5가 스마트폰 yaw인지 roll인지는 홀더와 카메라 외부파라미터가 없어 결정할 수 없다.**
4. `joints.stl`에는 150개 disconnected shell이 있다. 4개의 큰 link/bracket shell, 네 발형 base, A5 주위의 말단 지지 브래킷이 보인다. 6807ZZ와 일치하는 베어링 후보는 A2 뒤쪽 한 곳만 명확하다. 스마트폰을 실제로 물리는 clamp jaw/pad/lock 및 테이블 clamp 형상은 없다.
5. phorce의 참가자 런타임 제어는 임의 joint target이나 IK 명령이 아니라 **사전에 저장된 motion slot 하나를 선택해 재생하는 방식**이다. 따라서 이 로봇의 현실적인 MVP는 온라인 5축 servoing이 아니라, phorce Studio로 검증된 촬영 자세를 직접교시하고 Jetson이 상황에 맞는 슬롯을 1회 선택하는 구조다.
6. 5축으로 일반 6D camera pose를 모두 독립 제어할 수 없다. 촬영에서는 phone roll/portrait orientation 하나를 기계적으로 고정하고, optical axis의 yaw·pitch와 카메라 위치를 우선해야 한다. 실제로는 짧은 팔의 위치 변화보다 사용자 바닥 위치 안내와 촬영 프리셋이 더 큰 구도 변화를 담당해야 한다.
7. 다음 구현 세션의 첫 최소 기능은 **한 개의 검증된 상반신 프리셋을 한 번만 실행하고, 정지 확인 후 한 장을 촬영하는 end-to-end vertical slice**다. AI 구도 추천, 연속 IK, 여러 슬롯 자동 최적화는 그 뒤다.

## 1. 이번 세션에서 사용한 근거

저장소의 모든 파일을 유형에 맞게 다시 확인했다. 일반 인벤토리는 반복하지 않고, 5축 분석에 직접 영향을 주는 근거만 정리한다.

| 근거 | 이번 세션에서 사용한 내용 |
|---|---|
| `RESEARCH_REPORT.md` | 기존 5축 중심/축 추정, 제어 API 제한, 자료 누락 목록의 출발점 |
| `joints.stl` | shell 분리, phact 검출, 축·중심·거리, base/link/end bracket/bearing 후보 |
| `phact-401.stl`, `phact-401.pdf` | phact envelope와 체결 형상의 비교 기준; 전체 외형 약 Ø85×40 mm |
| `NSK_6807ZZ.stl` | 47×47×7 mm 베어링 envelope 비교 기준 |
| phact series catalog | 27/7.2 Nm peak/continuous, 150 rpm, 0.51 kg, FDCAN, 제품 내장 기능 |
| 최신 phorce quickstart/tutorial/manual/API reference | motion slot 계약, 1 kHz feedback, valid/QoS, single-flight, retry/recovery/safety |
| phorce Studio manual | 실제 axis discovery, 이름/영점, 직접교시, SD slot 저장, PID monitor |
| prototype JPEG 2개 | 손그림과 AI concept임을 확인; 실물 제작 증거로 사용하지 않음 |
| `Robot_Body_Adapter.stl` | 별도의 4-shell frame/adapter이나 `joints.stl`과의 조립 관계가 없음 |
| 나머지 PDF/PPTX/DXF/배포물 | 제어·행사 맥락 교차 확인. 현재 5축 camera kinematics를 추가로 확정할 자료는 없음 |

실제 하드웨어 사진은 없다. 두 JPEG는 각각 손그림과 `AI Concept Visualization`이다. 스마트폰 holder/clamp 전용 CAD, 조립 CAD, URDF, joint limit, camera mount transform도 없다.

최신 SDK 문서의 “현 기체 6축 장착”은 행사 공통 장비 설명이고, `joints.stl`에는 phact가 5개다. 사용자가 지정한 현재 제작물과 메시에는 5축이 일치하지만, **PCM이 실제로 검출하는 축 수는 phorce Studio에서 확인해야 한다.**

## 2. STL 분석 방법과 결과

### 2.1 방법

분석 스크립트는 STL triangle을 읽고 다음 순서로 처리한다.

1. 정확히 같은 vertex를 공유하는 triangle끼리 union하여 disconnected shell을 만든다.
2. `phact-401.stl`의 가장 큰 shell envelope와 `joints.stl` 각 shell의 정렬된 치수를 비교한다.
3. phact형 shell의 가장 짧은 bounding-box 방향을 회전축 후보로 사용한다.
4. `NSK_6807ZZ.stl`의 가장 큰 shell `47×47×7 mm`와 같은 방식으로 bearing 후보를 찾는다.
5. 검출 중심을 chain order로 정렬하고 중심간 거리를 계산한다.

이 방법은 축 **선의 방향**은 찾지만 회전의 `+/-` 부호, zero, 움직이는 쪽, hard stop은 찾지 못한다. STL은 조립 constraint와 물성을 담지 않기 때문이다.

### 2.2 메시 수치

| 항목 | 결과 | 판정 |
|---|---:|---|
| triangle | 365,424 | 메시 확인 |
| disconnected shell | 150 | 메시 확인 |
| bbox min | `(-182, -134.416, -8) mm` | 메시 확인 |
| bbox max | `(150, 134.416, 444) mm` | 메시 확인 |
| 중립 자세 전체 크기 | `332 × 268.831 × 452 mm` | 메시 확인 |
| phact형 본체 shell | 5개 | 메시 확인 |
| 명확한 6807ZZ형 shell | 1개 | 메시 확인 |

STL 자체에는 단위가 없다. phact의 85×40 mm 도면·카탈로그와 메시 크기가 일치하므로 mm로 해석했지만, 이것은 파일 포맷이 선언한 단위가 아니라 외부 치수와의 일치에 기반한 해석이다.

### 2.3 phact 검출, 중심, 축, 거리

참조 `phact-401.stl`의 전체 bbox는 약 `85×40×85 mm`이며, 가장 큰 housing shell은 `85×34×85 mm`다. `joints.stl`에서 정렬 치수가 `34×85×85 mm`인 shell이 정확히 5개 검출됐다.

| Joint | 중심 `(x,y,z)` mm | housing bbox mm | 중립 축 대표 벡터 | 다음 중심 벡터 mm | 거리 mm |
|---|---:|---:|---:|---:|---:|
| A1 | `(0, 0, 9)` | `85×85×34` | `[0,0,1]`, sign 미상 | `(0,17.5,120)` | 121.27 |
| A2 | `(0,17.5,129)` | `85×34×85` | `[0,1,0]`, sign 미상 | `(0,0,148)` | 148.00 |
| A3 | `(0,17.5,277)` | `85×34×85` | `[0,1,0]`, sign 미상 | `(0,0,108)` | 108.00 |
| A4 | `(0,17.5,385)` | `85×34×85` | `[0,1,0]`, sign 미상 | `(-108,-17.5,-17.5)` | 110.80 |
| A5 | `(-108,0,367.5)` | `85×85×34` | `[0,0,1]`, sign 미상 | — | — |

따라서 기존 추정 `A1: Z, A2: Y, A3: Y, A4: Y, A5: Z`는 **메시 envelope 기준으로 재검증됐다.** 여기서 벡터는 중립 자세의 base frame 표현이다. A2 같은 상위 관절이 움직이면 하위 관절의 공간축도 함께 회전한다.

중심 경로 길이는 A1→A5 약 `488.07 mm`, A2→A5 약 `366.80 mm`다. 이것은 최대 직선 reach가 아니라 중립 자세 중심 경로의 합이다.

### 2.4 링크와 브래킷 후보

다음은 큰 disconnected shell의 bbox와 위치로 분류한 후보이며, 원본 assembly constraint가 없으므로 정확한 part name은 확정하지 않는다.

| triangle | bbox 범위/크기 | 후보 역할 | 확실성 |
|---:|---|---|---|
| 16,574 | `300×268.831×74 mm`, z `-8..66` | 네 방향 발과 중앙 지지부를 포함한 base | 높음 |
| 17,022 | z `32..173.984`, A1~A2를 감쌈 | base-to-shoulder link/bracket | 중간 |
| 28,196 | z `104.016..321.984`, A2~A3를 감쌈 | shoulder-to-elbow link/bracket | 중간 |
| 18,700 | z `252.016..429.984`, A3~A4를 감쌈 | elbow-to-wrist link/bracket | 중간 |
| 18,700 | x `-152.984..24.984`, A4~A5를 감쌈 | wrist-to-terminal link/bracket | 중간 |
| 13,340 | x `-182..-83.016`, y 폭 150, z `333..444` | A5 주위 terminal support/mount bracket | 높음 |

이 shell들은 일부 actuator 주위를 감싸고 서로 영역이 겹친다. STL의 연결성만으로 “어느 링크가 어느 phact의 rotor에 체결되는지”를 확정할 수는 없다. 다만 serial chain의 공간 배치와는 일관된다.

### 2.5 베어링 후보

`NSK_6807ZZ.stl`의 기준 envelope `47×47×7 mm`와 1 mm 이내로 일치하는 shell은 다음 한 곳이다.

- 중심: 약 `(-0.005, -16.5, 129) mm`
- 크기: 약 `46.990×7×46.992 mm`
- 축: `Y`
- 위치 관계: A2 중심과 x/z가 같고 y 방향으로 34 mm 떨어진 phact housing의 뒤쪽

따라서 A2 shoulder의 반대편 지지 bearing 후보로 보는 것이 가장 자연스럽다. 다른 관절에서는 같은 envelope가 검출되지 않았다. 이것이 실제로 “베어링이 하나만 사용됐다”는 뜻은 아니다. 다른 베어링이 단순화된 형상, 브래킷에 병합된 형상, 다른 규격으로 모델링됐을 수 있다.

### 2.6 말단, 스마트폰 홀더, 베이스/클램프

- A5 주변에는 `98.98×150×111 mm` 범위의 큰 terminal bracket가 있다.
- 이 형상은 A5를 지지하거나 말단 장치를 장착하는 구조 후보지만, 스마트폰 폭을 조절하는 jaw, 미끄럼 방지 pad, spring/screw lock, 낙하 방지 tether는 확인되지 않는다.
- 별도 스마트폰 holder 파일도 없다. 따라서 terminal bracket의 어느 면에 폰이 붙고 렌즈가 어디를 향하는지 확정할 수 없다.
- base는 x/y 네 방향으로 발이 뻗은 floor/platform 구조다. 테이블 가장자리를 집는 clamp jaw나 screw는 없다.
- `Robot_Body_Adapter.stl`은 별도 4-shell 구조로 존재하지만 `joints.stl`과의 체결 위치가 문서화되지 않아 phone holder나 clamp로 귀속하지 않았다.

## 3. 실제 5축 관절 구조

| Joint | 추정 축 | 기구적 역할 | 움직이는 링크 | 카메라에 미치는 영향 | 예상 위험 |
|---|---|---|---|---|---|
| A1 | `±Z` | Base yaw | A2~A5와 말단 전체 | 카메라 중심의 수평 방위와 optical axis의 yaw를 함께 바꿈. 이상적으로 높이와 base 반경은 유지 | base 비틀림/전도, 케이블 감김, 발·주변물 충돌, yaw 한계 미상 |
| A2 | `±Y` | Shoulder pitch | A3~A5와 말단 전체 | 카메라 높이와 수평 reach를 가장 크게 바꾸고 pitch도 누적 | 가장 큰 중력 토크, bearing/브래킷 하중, 과열, base 간섭 |
| A3 | `±Y` | Elbow pitch | A4~A5와 말단 | 팔을 펴고 접어 reach/height를 바꾸며 terminal pitch도 바꿈 | 완전 신전/접힘 singularity, A2/A4 또는 링크 자기충돌, elbow snap-through |
| A4 | `±Y` | Wrist/link pitch | A5와 terminal bracket | A2+A3의 pitch를 보상해 카메라 기울기를 유지할 수 있음. A5 중심까지 110.8 mm offset이라 위치도 변함 | “순수 자세축”으로 오해, A3/A5 간섭, 말단 하중과 케이블 굽힘 |
| A5 | `±Z` | Terminal axial rotation | A5 이후 terminal mount/phone | 폰 중심이 축에서 벗어나면 원호 이동과 방향 회전이 동시에 발생. 축상에 있으면 위치는 거의 유지 | 실제 phone yaw/roll 역할 미확정, 케이블 꼬임, holder 충돌/폰 낙하 |

### 중력 토크에 대한 보수적 사전 경고

기존 보고서의 screening처럼 phact 자체 질량 `0.51 kg`만 놓고 A2 이후 세 actuator가 수평으로 놓이는 나쁜 자세를 가정하면 A2 actuator-only 정적 토크는 약 `3.86 Nm`다. 이는 phact-401 연속 토크 7.2 Nm의 약 54%다. 링크, 볼트, 베어링, terminal bracket, 스마트폰, holder, 동적 가속은 모두 빠진 하한 screening이다. 순간 27 Nm를 지속 설계값으로 사용하면 안 된다.

## 4. 관절 운동에 따른 스마트폰 카메라 변화

### 4.1 일반식

관절 `i`의 현재 공간축을 `a_i`, 축 위 중심을 `c_i`, 카메라 중심을 `p_C`, optical-axis 단위벡터를 `o_C`라 하면 작은 관절 변화의 1차 효과는 다음과 같다.

```text
dp_C/dq_i = a_i × (p_C - c_i)
do_C/dq_i = a_i × o_C
```

즉 회전축에서 멀리 떨어진 카메라일수록 같은 각도에 더 큰 위치 이동이 생긴다. 상위 관절일수록 더 많은 하위 링크를 움직인다.

A5만 보면, 중립 말단 transform을 안다는 가정 아래:

```text
p_C(q5) = c5 + R_z(q5) (p_C(0) - c5)
o_C(q5) = R_z(q5) o_C(0)
```

카메라가 A5 축에서 떨어져 있으면 중심도 원을 그린다. 따라서 A5를 무조건 “순수 roll”이라고 부를 수 없다.

### 4.2 지금 계산할 수 없는 것

정확한 camera pose에는 최소한 다음이 필요하다.

- 각 축의 실제 `+` 방향과 encoder zero
- link가 rotor/stator 중 어느 면에 체결되는지
- joint limit과 cable-limited range
- A5 이후 holder frame과 스마트폰 body frame transform
- 스마트폰 body에서 선택한 후면 렌즈 optical center/axis transform
- portrait/landscape 방향과 실제 사용 렌즈의 intrinsics

이 자료가 없으므로 정확한 DH/POE 모델, forward kinematics 수치, workspace, Jacobian rank map을 확정하지 않는다. 현재 제공 가능한 것은 중립 자세의 축 선과 중심 skeleton이다.

### 4.3 5-DoF 촬영 제약

일반 카메라 pose는 위치 3 + 방향 3으로 6 DoF다. 현재 기구가 5축이면 하나의 task freedom을 고정하거나 외부 조건으로 넘겨야 한다.

권장 우선순위는 다음과 같다.

1. **phone roll/화면 수평을 기계적으로 고정**한다. portrait/landscape는 촬영 시작 전 한 모드로 고정한다.
2. A1과 pitch chain으로 optical axis가 사람의 목표점(전신은 몸통 중심, 상반신은 얼굴/가슴 중심)을 보게 한다.
3. A2/A3으로 가능한 카메라 위치를 만들고 A4로 terminal pitch를 보상한다.
4. 팔 reach로 해결되지 않는 촬영 거리는 바닥 표시와 음성/UI의 사용자 위치 안내로 보완한다.
5. A5는 실제 holder calibration 결과에 따라 yaw 보정 또는 axial orientation 유지 중 하나로만 사용한다.

“roll 고정 + 카메라 위치 3 + look-at yaw/pitch 2”는 형식상 5개 task variable이지만, 실제 Jacobian이 모든 자세에서 full rank인 것은 아니다. A2~A4가 평행하므로 완전 신전/접힘 부근과 축이 겹치는 자세에서는 원하는 보정이 불가능하거나 매우 민감해질 수 있다.

## 5. phorce/phact 위의 제어 방식

### 5.1 도구의 역할 분리

```text
phact Studio
  개별 phact의 방향·원점·센서·System ID·제어 모드 설정 도구
  저장소에는 실제 접속/사용 절차가 없음

phorce Studio (Windows ↔ USB ↔ PCM)
  실제 축 검색/이름/영점 → 직접교시 → SD motion slot 저장/시험
  촬영 pose library를 만드는 오프라인 도구

Jetson + phorce SDK (EtherCAT ↔ PCM)
  1 kHz 상태 관측 + 저장된 motion ID 1개 선택/재생
  런타임 arbitrary joint target/IK/torque streaming은 공개되지 않음
```

축 방향, 이름, zero와 motion slot은 먼저 phorce Studio에서 실물 기준으로 확정해야 한다. 최신 SDK 문서의 축 수 설명이나 STL 순서를 PCM axis index로 간주하면 안 된다.

### 5.2 런타임 계약

- `/phorce/feedback`: 12칸 배열, 1 kHz, sensor-data/best-effort QoS. `axis[i].valid`인 축만 사용한다.
- `/phorce/status`: state, `physical_idle`, recovery 문맥. `IDLE`뿐 아니라 `COMPLETED + physical_idle`도 쉬는 상태다.
- `phorce list`: 실제 PCM에 적재된 슬롯이 정본이다.
- `PlayMotionSequence`: ID 1~50 중 한 개만. 큐와 multi-ID sequence가 없다.
- 실물 action feedback의 `current_motion_id=0`, `pvector_index=255`는 정상적인 고정값일 수 있어 진행/정지 판정에 쓰면 안 된다.
- 실물에서 `cancel()`, Ctrl+C, 터미널 종료는 수락된 모션을 멈추지 않는다. 즉시 정지는 물리 E-Stop뿐이다.
- 재시도 가능한 거절은 code 5/BUSY뿐이다. code 12/13은 사람 조치, 실행 중 error 15/16은 재전송 금지다.
- `~/arm`, `~/confirm`, `/phorce/submit_motion`, raw PDO/SDO, 저수준 `{target, torque_ff, Kp, Kd}`는 참가자 API가 아니다.

### 5.3 권장 제어 상태기계

```text
PARKED
  → WAIT_READY          버튼 1 이후 총 10초, status 확인
  → IDLE                valid axes, oper/fault/temp, slot 존재 확인
  → SELECT_PRESET       전신/상반신 + 키/인원 bin, hysteresis 적용
  → EXECUTING           single-flight play; 추가 명령 금지
  → SETTLING            실제 velocity가 충분히 낮아질 때까지 관측
  → FRAME_VALIDATE      사람이 여전히 frame 안에 있는지 재확인
  → CAPTURE             shutter 1회
  → COOLDOWN/IDLE       반복 트리거 차단

오류:
  BUSY → bounded wait 후 상태 재확인
  REJECT 12/13 → OPERATOR_REQUIRED
  ABORT/fault/stale/overheat suspicion → FAULT, 자동 재생 금지
```

1 kHz callback은 최신 상태만 lock-free/latest-value cache에 저장하고, 판단은 2~5 Hz의 느린 loop에서 한다. 조건이 참인 동안 반복하는 level-trigger가 아니라 `false→true`의 edge-trigger로 한 번만 보낸다.

촬영 pose는 다음 metadata를 가진 registry로 관리하는 것이 좋다.

```text
slot_id
composition = FULL | UPPER
subject_height_bin / group_size_bin
required_start_pose
expected_duration
phone_orientation
tested_clearance / tested_payload
camera calibration version
thermal cooldown
```

## 6. 전신샷과 상반신샷 관절 패턴

정확한 각도는 joint sign/limit, 폰 광축, 렌즈 화각, 설치 높이가 없어서 제시하지 않는다. 다음은 phorce Studio에서 직접교시할 **상대 패턴**이다.

| 목적 | A1 | A2/A3 | A4 | A5 | 사용자 위치 |
|---|---|---|---|---|---|
| 전신샷 | 사람 중심 방위로 맞춘 뒤 촬영 중 고정 | 팔을 비교적 펴 카메라-사람 거리를 늘리고, 검증된 몸통 높이에 camera center 배치 | A2+A3 누적 pitch를 상쇄하여 발~머리가 들어오는 목표점을 look-at | horizon/portrait orientation을 유지하는 고정값 | 더 먼 FULL 바닥 표식; 발이 잘리지 않는지 frame 재검증 |
| 상반신샷 | 같은 사람 중심 방위, 촬영 중 고정 | 팔을 접어 카메라를 가깝게 하거나 eye/chest 높이 preset으로 이동 | 얼굴 또는 가슴 중심을 보도록 terminal pitch 보정 | 같은 orientation 고정값 | 더 가까운 UPPER 표식; 얼굴 크기와 headroom 재검증 |
| 키 보정 | 작은 yaw 보정만 | `LOW/MID/HIGH` 높이 bin 사이에서 검증된 slot 선택 | 각 height slot에 저장된 pitch 사용 | 고정 | 사용자를 좌우/앞뒤로 미세 안내 |
| 단체샷 | 중앙 방위 | reach보다 거리 확보를 우선; 넓은 구도 slot | 그룹 중심을 look-at | 고정 | 더 멀리 이동시키고 전원이 넓은 box 안에 들어온 뒤 촬영 |

pitch chain의 부호와 link frame이 일반적인 경우 terminal pitch를 유지하는 보상 패턴은 개념적으로 다음과 같다.

```text
Δq4 ≈ -(Δq2 + Δq3)
```

실제 부호와 zero offset은 실물에서 달라질 수 있으므로 이 식을 그대로 명령값으로 쓰지 말고, 직접교시 pose의 변화 관계를 설명하는 패턴으로만 사용한다.

A2→A5 중심 경로 자체가 약 367 mm라서 팔만으로 일반 촬영 거리 전체를 바꾸기는 어렵다. 전신/상반신 차이는 **로봇팔 + 고정 렌즈 + 사용자 거리 표식**의 조합으로 만들어야 한다. digital zoom은 화질 저하가 있으므로 마지막 보조 수단으로 둔다.

권장 초기 slot 세트는 연속 IK가 아니라 다음처럼 작고 검증 가능한 조합이다.

```text
FULL_LOW, FULL_MID, FULL_HIGH
UPPER_LOW, UPPER_MID, UPPER_HIGH
PARK / SAFE_RETURN
```

각 slot은 같은 안전한 시작 자세에서 출발하도록 교시한다. 임의 현재 자세에서 바로 재생해도 충돌이 없는지는 문서가 보장하지 않는다.

## 7. 구현 edge case

### 7.1 기구/하중

- STL은 5축인데 최신 공통 SDK 문서는 6축 기체를 설명한다. axis count/index/name을 hard-code하면 안 된다.
- A2~A4 평행축이 완전 신전 또는 접힘에 가까우면 Jacobian rank/condition이 나빠지고 작은 구도 변화에 큰 joint 변화가 필요할 수 있다.
- A4는 orientation-only wrist가 아니다. A5 중심까지 offset이 있어 A4 회전은 camera position도 바꾼다.
- A5 역할과 camera offset이 미확정이다. 폰이 축에서 멀면 A5 회전 중 큰 원호를 그린다.
- links, terminal bracket, phone의 질량/CoM과 phact 허용 radial/axial load가 없다.
- 3D print의 layer 방향, creep, bolt pull-out, backlash, 유격이 구도 흔들림과 공진을 만든다.
- base는 clamp가 아니라 네 발이다. 바닥/테이블 고정 없이 reach를 늘리면 전도·미끄럼 모멘트가 커진다.
- cable service loop와 strain relief가 없다. A1/A5 반복 회전으로 USB/충전 케이블이 감길 수 있다.
- phone clamp와 tether가 없다. 충격 또는 급정지 시 스마트폰 낙하가 가장 큰 말단 위험이다.
- self-collision, base/table collision, 사람과의 충돌, hard stop은 mesh만으로 안전 범위를 만들 수 없다.

### 7.2 열과 제어

- 제품 카탈로그는 phact의 “액티브 온도 제한” 기능을 설명하지만, 행사 문서는 과열 자동 차단이 없고 `temp_c`는 표시용이라고 경고한다. 촬영 시스템 안전은 자동 shutdown이 있다고 가정하면 안 된다.
- 유지 자세가 중력에 불리하거나 기구가 걸리면 position error와 전류가 지속되어 발열한다.
- level-trigger 조건으로 같은 slot을 연속 재생하면 발열과 기계 피로가 누적된다.
- BUSY를 무한 retry하면 실제로 앞 모션이 실행 중인지, latch가 걸렸는지 구분하기 어려워진다.
- action client timeout 또는 Ctrl+C 뒤에도 로봇은 움직일 수 있다.
- Studio USB 세션이 PCM을 점유하면 runtime motion이 code 12/error 20으로 거절될 수 있다.
- 영점 변경 뒤 기존 slot은 잘못된 자세를 재생할 수 있다. calibration version과 slot version을 함께 관리해야 한다.
- 정전/재부팅 뒤 monitor→action server 순서와 버튼 1/10초 준비가 다시 필요하다.
- ROS 2가 같은 Wi-Fi의 다른 팀과 합쳐질 수 있다. `ROS_LOCALHOST_ONLY=1`과 duplicate server 진단이 필요하다.

### 7.3 상태 관측

- `axis[0]` 또는 문서 예제의 특정 index를 사용하면 실제 축을 놓친다. 12칸에서 `valid`를 찾아야 한다.
- `!stale`은 valid의 대체가 아니다. 한 번도 데이터가 안 온 축도 stale=false일 수 있다.
- feedback QoS가 reliable이면 오류 없이 아무 데이터도 안 올 수 있다.
- action feedback의 motion ID/P-vector index는 실물 진행률로 사용할 수 없다.
- “모션 result 도착”과 “사진을 찍어도 될 만큼 진동이 가라앉음”은 다르다. valid 축 velocity와 영상 blur를 별도로 확인해야 한다.

### 7.4 촬영/인식

- 사람이 motion 실행 중 이동하면 도착 pose가 더 이상 유효하지 않다. 이동 중 재계획이 불가능하므로 도착 후 frame을 다시 검증한다.
- 전신/상반신 분류가 경계에서 흔들리면 slot ping-pong이 난다. hysteresis와 최소 유지시간이 필요하다.
- 여러 사람의 center/height, 가려짐, 앉은 자세, 어린이, 휠체어 사용자는 별도 composition rule이 필요하다.
- 스마트폰의 렌즈 전환, OIS, autofocus, auto-exposure, orientation metadata가 camera model과 shutter timing을 바꿀 수 있다.
- rear-camera preview와 shutter 통신 방식이 없다. 폰→iPad preview 지연과 실제 capture timestamp를 구분해야 한다.
- holder가 렌즈나 flash를 가리거나 wide lens 화각에 들어올 수 있다.
- portrait/landscape를 소프트웨어 EXIF 회전만으로 바꾸면 실제 optical framing은 달라지지 않는다.

### 7.5 복구

- 버튼 2는 단순 상태 reset이 아니라 로봇을 종료 자세로 약 3초간 움직일 수 있다. 주변을 비운 뒤 사용한다.
- E-Stop 뒤에는 버튼 해제→로봇 전원 재인가→monitor 재시작→action server→버튼 1→10초 순서가 필요하다.
- error 15/16, 이상음, 탄내, 온도 상승은 자동 재시도하지 않는다.

## 8. 따라야 할 소프트웨어와 제어 패턴

1. **Calibrate, teach, then select**: online IK보다 실제 5축 mapping/zero/camera extrinsic을 기록하고 검증된 slot을 직접교시한다.
2. **Fast observer, slow supervisor**: 1 kHz feedback callback은 저장만, 2~5 Hz supervisor가 판단과 play를 담당한다.
3. **Single-flight command**: 한 번에 action 하나, result와 실제 settle을 확인한 뒤 다음 상태로 간다.
4. **Edge-trigger + cooldown**: 조건의 변화에 한 번만 실행하고 재무장 조건과 휴지시간을 둔다.
5. **Explicit finite-state machine**: ready/idle/executing/settling/capture/operator-required/fault를 명시한다.
6. **Positive validity**: `valid && oper && !fault`인 실제 축 집합과 기대한 5축 mapping이 일치할 때만 동작한다.
7. **No hidden progress inference**: action feedback 고정값, timeout, 화면 상태로 실제 정지를 추측하지 않는다.
8. **Preset registry with provenance**: slot을 composition, payload, zero version, camera calibration, test 결과와 함께 버전 관리한다.
9. **Visual verify after motion**: motion 전에 안전/사람 위치, motion 뒤에 frame/진동/노출을 다시 확인한다.
10. **Human-in-the-loop recovery**: code 12/13과 fault를 숨기지 않고 UI에 물리 버튼 절차를 정확히 표시한다.
11. **Fail closed**: stale, 축 수 불일치, slot 없음, camera preview 끊김, 높은 온도 또는 holder 상태 불명에서는 촬영 모션을 보내지 않는다.
12. **Separate composition from actuator control**: AI는 `FULL_MID` 같은 검증된 skill/slot을 선택하고 raw angle이나 torque를 생성하지 않는다.

## 9. 다음 구현 세션의 최소 기능

### 첫 vertical slice: `ONE_SHOT_UPPER_MID`

고정된 한 명, 표시된 한 위치, 한 스마트폰 방향, 한 렌즈, 한 상반신 구도로 범위를 제한한다.

1. phorce Studio에서 실제 5개 axis ID↔A1~A5, sign, zero를 기록한다.
2. dummy phone payload로 `PARK → UPPER_MID` 한 slot을 저속 직접교시하고 실물에서 충돌/전류/온도/진동을 확인한다.
3. 앱은 manual “촬영 시작” edge 하나만 받는다. 아직 사람 검출/AI 선택은 넣지 않는다.
4. `doctor/list/status`, expected valid-axis set, fault, `physical_idle`을 preflight한다.
5. slot을 정확히 한 번 재생한다. BUSY 외 자동 retry는 하지 않는다.
6. result 뒤에도 5개 valid axis의 속도가 충분히 안정됐는지 확인하고, camera frame을 한 번 재검증한다.
7. 스마트폰 shutter를 1회 트리거하고 사진 한 장의 저장 성공을 표시한다.
8. cooldown 후에만 다시 arm한다. operator-required/fault는 명시적인 복구 화면으로 보낸다.

### 완료 기준

- 같은 zero/calibration에서 연속 10회 중 잘못된 중복 재생 0회
- 실행 중 추가 motion request 0회
- 각 실행 전후 expected 5축 valid 확인
- 사람/폰/베이스 충돌 0회, holder 이동/풀림 0회
- 10장 모두 얼굴과 상반신이 정의한 frame 영역 안에 있고 심한 motion blur 없음
- 온도·전류는 로그로 남기며 허용치는 제조사/운영진이 정한 값 사용
- 실패 시 로봇 움직임을 숨기지 않고 operator action을 화면에 표시

이 한 경로가 안정된 뒤 `FULL_MID`, height bins, 사람 검출, 자동 preset selection을 순서대로 추가한다. 첫 세션부터 continuous tracking이나 learned control을 넣는 것은 현재 공개 제어 계약과 맞지 않는다.

## 10. 실물에서 반드시 확인할 항목

| 항목 | 이유 | 확인 방법 |
|---|---|---|
| PCM이 검출하는 실제 축 수/ID | STL 5축 vs 공통 문서 6축 | phorce Studio read-only inventory |
| A1~A5 encoder sign/zero | STL은 sign/zero를 담지 않음 | 서보 OFF 소각도 이동 + feedback 기록 |
| rotor/stator 체결과 실제 moving link | disconnected STL로 확정 불가 | 각 축 하나씩 움직이는 영상/표식 |
| joint/cable limit | workspace와 self-collision 계산에 필수 | 저속·소범위에서 보수적 limit 측정 |
| A5→holder→camera transform | A5의 yaw/roll 역할과 optical axis 결정 | holder 치수 + checkerboard/pose calibration |
| phone+holder 질량/CoM | A2/A3 토크와 진동 | 분리 계량과 balance 측정 |
| base 고정/전도 margin | 현재 메시가 clamp가 아님 | 실제 설치 사진, 체결, 최대 reach 정적 시험 |
| bearing 실제 배치 | 메시에는 A2 후보 하나만 명확 | 조립 사진/BOM/분해 확인 |
| slot 시작 자세 계약 | 임의 자세 실행 충돌 방지 | Studio/운영진 확인 + 실물 반복 시험 |
| shutter/preview 계약 | end-to-end 촬영에 필수 | 사용할 phone OS/app/network 방식 확정 |

## 11. 산출물

- 분석 스크립트: [`analysis/session2/analyze_stl.py`](analysis/session2/analyze_stl.py)
- 수치 요약: [`analysis/session2/output/summary.json`](analysis/session2/output/summary.json)
- 전체 shell 표: [`analysis/session2/output/shells.csv`](analysis/session2/output/shells.csv)
- 정면: [`analysis/session2/output/front.png`](analysis/session2/output/front.png)
- 측면: [`analysis/session2/output/side.png`](analysis/session2/output/side.png)
- 상면: [`analysis/session2/output/top.png`](analysis/session2/output/top.png)
- A1~A5, 축 선, skeleton 통합: [`analysis/session2/output/annotated_views.png`](analysis/session2/output/annotated_views.png)
- shell별 색상 분리: [`analysis/session2/output/shell_components.png`](analysis/session2/output/shell_components.png)
- 3D kinematic skeleton: [`analysis/session2/output/kinematic_skeleton.png`](analysis/session2/output/kinematic_skeleton.png)

재현 명령:

```bash
MPLCONFIGDIR=/tmp/mplconfig python3 analysis/session2/analyze_stl.py \
  --assembly 'roboticus/3d print/joints.stl' \
  --phact 'roboticus/3d print/phact-401.stl' \
  --bearing 'roboticus/3d print/NSK_6807ZZ.stl' \
  --output analysis/session2/output
```

## 최종 판정

`Z–Y–Y–Y–Z`와 5개 관절 중심은 메시로 강하게 확인됐다. 이 구조는 base yaw + 3축 planar pitch positioning + terminal axial rotation의 촬영용 5축 chain으로 해석할 수 있다. 그러나 phone clamp, camera extrinsic, sign/zero/limit, 실제 axis mapping이 없으므로 “A5=phone roll”, 정확한 camera workspace, 전신/상반신 각도값을 확정하면 안 된다.

현재 phorce 계약에서 맞는 구현은 **실물에서 직접교시한 안전한 camera-pose slot을 상태기계가 한 번씩 선택하고, 실제 정지와 frame을 재검증한 뒤 촬영하는 시스템**이다. 첫 구현은 한 상반신 프리셋의 안전한 단발 촬영이어야 한다.
