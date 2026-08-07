# Jetson에서 PHACT 제어하기

## 1. 제어 경계

P-Vector는 `[yd, Ltraj, s0, sd]`입니다. `yd`는 출력축 목표 각도(degree),
`Ltraj`는 궤적 길이, `s0`/`sd`는 가속/감속 파라미터입니다. 이 값은
`MotionMap.csv`를 작성해 로봇의 모션 슬롯에 미리 적재할 때 사용합니다.

Jetson 참가자 코드의 공개 구동 API는 P-Vector 직접 전송이 아니라, 적재된
모션 슬롯 `1..50` 중 하나를 `phorce.play(id)`로 재생하는 방식입니다.

## 2. 모션 준비

1. P-Vector로 `full_body`, `upper_body`, `product_closeup` 세 동작을 작성합니다.
2. Phorce Studio/운영진 절차로 각 동작을 로봇 SD 카드의 슬롯에 적재합니다.
3. Jetson에서 `phorce list`를 실행해 실제 슬롯 ID와 이름을 확인합니다.
4. 처음에는 속도와 이동량을 낮게 잡고, 주변을 비운 상태에서 각 슬롯을 CLI로
   한 번씩 검증합니다: `phorce play <ID>`.

## 3. Jetson과 로봇 스택 기동

한 번만 설정하고 열린 터미널을 모두 다시 엽니다.

```bash
echo 'export ROS_LOCALHOST_ONLY=1' >> ~/.bashrc
```

로봇 전원을 먼저 켠 뒤 아래 순서로 각각 별도 터미널에서 실행합니다.

```bash
# 터미널 1
ros2 run agx_phorce_bridge phorce_monitor \
  --ros-args -p nic:=eno1 -p mode:=command -p axes:=2 -p mbx_enabled:=true

# 터미널 2
ros2 run agx_motion_slot motion_action_server --ros-args -p backend:=ecat
```

세 번째 터미널에서 확인합니다.

```bash
phorce doctor
ros2 topic hz /phorce/feedback
phorce list
```

기체의 1번 버튼을 0.6초 이상 누르고 총 10초 기다린 다음,
`phorce status`의 `physical idle True`를 확인합니다.

## 4. 프로젝트 설정

```bash
cd ~/1st-robot-hackathon_geekseek
cp config/jetson-phorce.example.yaml config/jetson-phorce.yaml
```

`config/jetson-phorce.yaml`의 `phorce_motion_ids`를 `phorce list`에서 확인한
실제 ID로 바꿉니다. 예시의 `1, 2, 3`을 확인 없이 그대로 쓰면 안 됩니다.

## 5. 실행

ROS 2 환경을 source한 터미널에서 실행합니다.

```bash
source /opt/ros/humble/setup.bash
python3 -m pip install -e '.[dev]'
python3 -m geekseek --config config/jetson-phorce.yaml
```

촬영 상태에서 기존 `Coordinator`가 의미 포즈를 순서대로 요청하면
`PhorceRobot`이 설정된 슬롯을 재생하고, 성공 결과가 온 뒤에만 촬영합니다.

## 6. 안전 및 실패 처리

- 즉시 정지는 물리 E-Stop만 가능합니다. Ctrl+C나 취소는 수락된 모션을
  멈추지 못합니다.
- `MotionBusy`만 1초 간격으로 제한 재시도합니다.
- 영점/복구 필요(`MotionRejected`), 중단(`MotionAborted`), 연결 실패는 자동
  연타하지 않고 워크플로를 실패 상태로 보냅니다.
- 모터가 뜨겁거나 탄내/이상음이 나면 즉시 E-Stop을 누릅니다. 자동 과열 차단이
  없습니다.
- `/phorce/submit_motion`, `~/arm`, `~/confirm`은 내부 인터페이스이므로 직접
  호출하지 않습니다.

## 7. 손 교시 자세와 휴대폰 프레임 함께 저장

Jetson에서 ROS 2 환경을 불러온 뒤 자세 캡처 서버를 실행합니다. `--axes`는
phorce Studio에서 확인한 실제 A1~A5 인덱스로 바꿔야 합니다.

```bash
source /opt/ros/humble/setup.bash
python3 scripts/capture_pose_samples.py --axes 0,1,2,6,8
```

현재 5축 기체에서 확인한 `axis_valid_mask=0x147`의 유효 인덱스는
`0,1,2,6,8`입니다. 다른 PCM을 연결하면 `valid=true`인 축에 맞춰 `--axes`를
다시 지정합니다.

1. 휴대폰 Safari에서 `https://<JETSON-IP>:8444/phone`을 열고 카메라를 허용합니다.
2. Jetson에서 `python3 scripts/pose_capture_gui.py --server https://127.0.0.1:8444`를 실행합니다.
3. Pygame 창의 iPhone 실시간 영상을 보며 로봇팔을 원하는 자세로 움직인 뒤 멈춥니다.
4. Pygame 창에서 Space를 누릅니다.

사진과 캡처 시점/수신 시점의 5축 각도 JSON은 `calibration/`에 같은 이름으로
저장됩니다. 기본 설정은 어느 축이든 `0.5 deg/s`보다 빠르면 저장을 거부합니다.
브라우저가 자체 서명 인증서를 경고하면 휴대폰과 Jetson 양쪽에서 한 번씩 접속을
허용해야 WebSocket 카메라 연결이 성립합니다.
