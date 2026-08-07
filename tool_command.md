# iPhone 실시간 Pose 기록 도구

## 현재 영점 offset

힘이 들어간 Studio 영점 자세에서 저장한
`pose_20260808_045958_698478` 샘플을 기준으로 사용한다.

| PCM 축 | raw offset (rad) | raw offset (deg) |
|---:|---:|---:|
| 0 | 2.5615 | 146.763139 |
| 1 | 0.4960 | 28.418707 |
| 2 | -0.7200 | -41.252961 |
| 6 | -0.8340 | -47.784680 |
| 8 | 0.6860 | 39.304905 |

설정 파일은 `config/pose-zero-offsets.json`이다. Pygame에는
`wrap(raw angle - raw offset)`으로 계산한 영점 보정 각도를 크게 표시하고 raw
각도를 함께 표시한다. 캡처 JSON에도 두 값을 모두 보존한다.

## 실행

버튼 1을 누르지 않고 로봇 구동 출력이 없는 `safe_op`에서 실행한다.

```bash
# 터미널 1: PCM 피드백만 읽기
source /opt/ros/humble/setup.bash
ros2 run agx_phorce_bridge phorce_monitor \
  --ros-args -p nic:=eno1 -p mode:=safe_op -p axes:=5 -p mbx_enabled:=true

# 터미널 2: iPhone live/pose 서버
cd /home/phorce/Desktop/hackton/1st-robot-hackathon_geekseek
source /opt/ros/humble/setup.bash
python3 scripts/capture_pose_samples.py --axes 0,1,2,6,8 --port 8454

# 터미널 3: Pygame GUI
cd /home/phorce/Desktop/hackton/1st-robot-hackathon_geekseek
python3 scripts/pose_capture_gui.py --server https://127.0.0.1:8454
```

iPhone Safari에서 `https://<JETSON-IP>:8454/phone`을 열고 카메라를 허용한다.
카메라 프레임은 항상 세로 3:4 비율의 480×640 중앙 크롭으로 전송한다. iPhone과
Pygame 미리보기의 3분할 grid는 구도 확인용이며 저장 JPG에는 포함하지 않는다.
카메라 선택(`facingMode=environment`)과 JPEG 품질(0.92)은 기존 iPhone 서버
캡처 방식과 동일하다.

서버는 기본적으로 Jetson의 `/dev/video0`(OpenCV index 0)을 640×480, 15fps로
읽고 MediaPipe skeleton을 약 5fps로 계속 추론한다. 다른 웹캠이면 서버 명령에
`--webcam-index 1`을 추가한다. Pygame의 `Webcam skeleton` 표시가 초록색이어야
Space 저장이 가능하다.

## 조작

- `Space`: 현재 iPhone 프레임, 웹캠 원본, 웹캠 skeleton 결과와 5축 pose를
  `calibration/`에 같은 sample ID로 저장
- `Esc`: Pygame 종료
- 저장 조건: 모든 축 `valid=true`, 피드백 최신, 각속도 `0.5 deg/s` 이하

저장 파일은 다음 네 개다.

- `pose_....jpg`: 3:4 iPhone 이미지
- `pose_...._webcam.jpg`: 웹캠 원본 이미지
- `pose_...._skeleton.jpg`: MediaPipe skeleton overlay 이미지
- `pose_....json`: 각도, 영점, 웹캠 감지 결과와 세 이미지 파일명

영점을 바꾸려면 원본 raw 데이터를 유지한 채
`config/pose-zero-offsets.json`만 수정한다. 이 서버는 PCM 데이터를 읽기만 하며
로봇 구동 명령을 보내지 않는다.
