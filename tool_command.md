# Pose 측정과 비교

## 1. Pose 측정

```bash
# 터미널 1
source /opt/ros/humble/setup.bash
ros2 run agx_phorce_bridge phorce_monitor \
  --ros-args -p nic:=eno1 -p mode:=safe_op -p axes:=5 -p mbx_enabled:=true

# 터미널 2
source /opt/ros/humble/setup.bash
python3 scripts/capture_pose_samples.py \
  --axes 0,1,2,6,8 --port 8454 \
  --csv-file calibration/trial_01.csv

# 터미널 3
python3 scripts/pose_capture_gui.py --server https://127.0.0.1:8454
```

iPhone에서 `https://<JETSON-IP>:8454/phone`을 연다. Pygame에서 원하는 위치마다
`Space`를 누르면 개수 제한 없이 `trial_01.csv`에 한 행씩 추가된다.

CSV 한 행에는 영점 보정된 5DOF 각도, skeleton이 표시된 webcam 이미지 파일명,
iPhone 이미지 파일명이 저장된다.

## 2. Pose 비교

```bash
python3 scripts/pose_dataset_viewer.py calibration/trial_01.csv
```

- `←/→`: 비교할 pose 이동
- `Space`: 현재 pose를 기준 A로 지정
- `R`: CSV 다시 읽기
- `Esc`: 종료
