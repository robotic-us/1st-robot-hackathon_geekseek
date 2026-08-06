# Geekseek RViz fake robot

전체 STEP의 크기와 6개 액추에이터 구성을 단순화한 테스트용 관절 모델이다. 앱의 `RvizRobot`은
`/geekseek/fake_robot/target`에 `frame.full_body`, `frame.upper_body`,
`frame.product_closeup` 같은 의미 기반 포즈를 발행한다.

```bash
source /opt/ros/humble/setup.bash
colcon build --base-paths ros --symlink-install
source install/setup.bash
ros2 launch geekseek_fake_robot display.launch.py
```

다른 터미널에서 상태 머신 전체 흐름을 실행한다.

```bash
PYTHONPATH="src:${PYTHONPATH}" python3 -m geekseek --config config/rviz.yaml --demo
```

ROS Humble는 시스템 Python 3.10을 사용한다. Conda Python을 함께 쓸 때도 위처럼 기존 `PYTHONPATH`를
보존해야 ROS CLI 패키지를 찾을 수 있다.
