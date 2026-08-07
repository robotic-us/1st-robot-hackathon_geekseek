# 명령어 모음

프로젝트를 실행·개발·검증할 때 쓰는 명령어를 한 곳에 모았다. 더 자세한 배경은
[`context/README.md`](../context/README.md)와 [`docs/PHACT_CONTROL.md`](PHACT_CONTROL.md)를 참고.

## 설치

```bash
python3 -m pip install -e '.[dev]'
```

STEP 메시를 다시 생성할 때만 CAD 의존성이 추가로 필요하다.

```bash
python3 -m pip install -e '.[cad]'
```

## 서버 실행

```bash
python3 -m geekseek --config config/dev.yaml
```

| 설정 파일 | 용도 |
|---|---|
| `config/dev.yaml` | 기본 개발용 — 로봇 없이 fake robot으로 전체 흐름 확인 |
| `config/local-demo-no-robot.yaml` | 웹캠 감지 + iPad UI만(1~4단계) 노트북 하나로 검증 |
| `config/local-demo.yaml` | RViz 로봇 등 포함한 전체 로컬 데모 |
| `config/rviz.yaml` | STEP 기반 5축 RViz fake robot 연동 |
| `config/jetson-phorce.example.yaml` | Jetson 실기기용 예시 설정 (복사해서 `jetson-phorce.yaml`로 사용) |

UI 없이 상태 머신 한 사이클만 헤드리스로 돌리려면 `--demo`를 추가한다.

```bash
python3 -m geekseek --config config/dev.yaml --demo
```

접속 주소 (서버 실행 후, `config/dev.yaml`처럼 `web.port: 8000`이고 `ssl_*` 설정이 없는 경우):

- 개발 화면: `http://localhost:8000/debug`
- iPad 1: `http://<서버-IP>:8000/face`
- iPad 2: `http://<서버-IP>:8000/guide`

`local-demo*.yaml`/`jetson-phorce.yaml`처럼 `web.port: 8443` + `ssl_keyfile`/`ssl_certfile`를 쓰는
설정은 `https://<서버-IP>:8443/face`·`/guide`·`/debug`로 접속한다. `<서버-IP>`는 서버를 실행한 기기에서
`hostname -I`로 확인하고, iPad가 그 기기와 같은 Wi-Fi 대역에 있어야 한다. 인증서가 없으면 (`certs/`
디렉터리가 비어 있으면) 이 설정들은 서버 시작 자체가 실패하므로 먼저 만들어둔다.

```bash
mkdir -p certs
openssl req -x509 -newkey rsa:2048 -keyout certs/key.pem -out certs/cert.pem \
  -days 3650 -nodes -subj "/CN=geekseek"
```

자체서명 인증서라 iPad Safari에서는 "안전하지 않음" 경고가 뜬다 — "고급 → 계속 진행"으로 넘어가면 된다.

`runtime.debug_window: true`(`local-demo*.yaml`)를 쓰면 pygame 미션컨트롤 창(`scripts/mission_control.py`)이
서버와 같은 파이썬 인터프리터로 자동 실행된다. 창이 안 뜨면 그 인터프리터에 `pygame`이 없거나(설치),
`mediapipe` import가 깨져 있는 경우가 많다 — 특히 Jetson 등 시스템 패키지로 깔린 `matplotlib`이 pip로
설치한 `numpy>=2`와 ABI 충돌을 내며 `mediapipe.tasks.python.vision`을 못 불러오는 경우가 있는데,
사용자 site-packages에 최신 `matplotlib`을 설치하면(시스템 패키지보다 우선순위가 높아서) 해결된다.

```bash
python3 -m pip install --user --upgrade pygame matplotlib
```

원격(예: SSH)으로 서버를 띄우면서 pygame 창을 물리 디스플레이에 띄우려면 그 세션의 `DISPLAY`/`XAUTHORITY`를
로그인된 세션 값으로 맞춰줘야 한다 (예: `DISPLAY=:1 XAUTHORITY=/run/user/<uid>/gdm/Xauthority`).

## 테스트

```bash
pytest tests/
```

## 개발용 스크립트

```bash
# 노트북 웹캠으로 MediaPipe 스켈레톤 오버레이 실시간 확인
python3 scripts/live_webcam_pose.py [camera-index]

# 웹캠 인식(접근/정위치) 단독 스모크 테스트
python3 scripts/test_webcam_perception.py [camera-index] [seconds]

# 아이폰 Safari 웹앱 캡처 단독 테스트 서버
python3 scripts/phone_capture_server.py [port]
# 다른 터미널에서 트리거
curl -X POST https://<이 머신 IP>:<port>/trigger -k

# Pushcut 웹훅으로 아이폰 Shortcuts 자동화 트리거 (경로 3, 현재는 미채택)
python3 scripts/trigger_pushcut.py <webhook-url>
```

## RViz fake robot

```bash
source /opt/ros/humble/setup.bash
colcon build --base-paths ros --symlink-install
source install/setup.bash
ros2 launch geekseek_fake_robot display.launch.py
```

옵션:

```bash
ros2 launch geekseek_fake_robot display.launch.py move_seconds:=2.0
ros2 launch geekseek_fake_robot display.launch.py use_rviz:=false
ros2 launch geekseek_fake_robot display.launch.py use_fake_robot:=false   # 외부 /joint_states 진단용
```

다른 터미널에서 상태 머신 전체 흐름 실행:

```bash
PYTHONPATH="src:${PYTHONPATH}" python3 -m geekseek --config config/rviz.yaml --demo
```

### STEP 메시 재생성 (STEP 원본이 바뀐 경우에만)

```bash
python3 tools/extract_step_links.py \
  assets/cad/Assemble_CAM.step \
  ros/geekseek_fake_robot/meshes
```

## Jetson 실기기 (phorce SDK)

로봇 전원을 켠 뒤 별도 터미널에서 순서대로:

```bash
# 터미널 1
ros2 run agx_phorce_bridge phorce_monitor \
  --ros-args -p nic:=eno1 -p mode:=command -p axes:=2 -p mbx_enabled:=true

# 터미널 2
ros2 run agx_motion_slot motion_action_server --ros-args -p backend:=ecat

# 터미널 3 — 상태 확인
phorce doctor
ros2 topic hz /phorce/feedback
phorce list
phorce status
```

모션 슬롯 검증(주변을 비운 상태에서, 속도/이동량 낮게):

```bash
phorce play <ID>
```

프로젝트 설정 후 실행:

```bash
cd ~/1st-robot-hackathon_geekseek
cp config/jetson-phorce.example.yaml config/jetson-phorce.yaml
# config/jetson-phorce.yaml의 phorce_motion_ids를 phorce list 결과로 수정

source /opt/ros/humble/setup.bash
python3 -m pip install -e '.[dev]'
python3 -m geekseek --config config/jetson-phorce.yaml
```

안전: 즉시 정지는 물리 E-Stop만 가능하다 — Ctrl+C나 취소는 이미 수락된 모션을 멈추지 못한다.
