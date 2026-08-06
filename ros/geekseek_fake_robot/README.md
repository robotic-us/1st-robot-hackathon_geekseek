# Geekseek RViz fake robot

전체 STEP의 크기와 6개 액추에이터 구성을 단순화한 테스트용 관절 모델이다. 앱의 `RvizRobot`은
`/geekseek/fake_robot/target`에 `frame.full_body`, `frame.upper_body`,
`frame.product_closeup` 같은 의미 기반 포즈를 발행하고, `completed:<pose>` 피드백을 받은 뒤에만
상태 머신을 `GUIDING`으로 전환한다. RViz의 청록색 화살표는 카메라가 보는 방향이고 상단 라벨은 현재
의미 포즈와 이동 상태다.

```bash
source /opt/ros/humble/setup.bash
colcon build --base-paths ros --symlink-install
source install/setup.bash
ros2 launch geekseek_fake_robot display.launch.py
```

이동 시간을 바꾸거나 GUI 없이 노드만 검증할 수도 있다.

```bash
ros2 launch geekseek_fake_robot display.launch.py move_seconds:=2.0
ros2 launch geekseek_fake_robot display.launch.py use_rviz:=false
```

다른 터미널에서 상태 머신 전체 흐름을 실행한다.

```bash
PYTHONPATH="src:${PYTHONPATH}" python3 -m geekseek --config config/rviz.yaml --demo
```

ROS Humble는 시스템 Python 3.10을 사용한다. Conda Python을 함께 쓸 때도 위처럼 기존 `PYTHONPATH`를
보존해야 ROS CLI 패키지를 찾을 수 있다.
