from __future__ import annotations

import math
import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import String


JOINT_NAMES = [
    "base_yaw_joint",
    "shoulder_pitch_joint",
    "elbow_pitch_joint",
    "wrist_yaw_joint",
    "wrist_pitch_joint",
    "camera_roll_joint",
]

POSES = {
    "home": (0, -15, 35, 0, -20, 0),
    "frame.full_body": (0, 10, 30, 0, -40, 0),
    "frame.upper_body": (-20, -5, 55, 10, -35, 0),
    "frame.product_closeup": (25, -20, 70, -15, -25, 5),
    "safe.retreat": (0, -35, 65, 0, -30, 0),
}


class FakeRobotNode(Node):
    def __init__(self) -> None:
        super().__init__("geekseek_fake_robot")
        self.declare_parameter("move_seconds", 1.2)
        self.move_seconds = float(self.get_parameter("move_seconds").value)
        self.publisher = self.create_publisher(JointState, "/joint_states", 10)
        self.status_publisher = self.create_publisher(String, "/geekseek/fake_robot/status", 10)
        self.create_subscription(String, "/geekseek/fake_robot/target", self.on_target, 10)
        self.timer = self.create_timer(1.0 / 30.0, self.tick)

        self.start = self._radians(POSES["home"])
        self.current = list(self.start)
        self.target = list(self.start)
        self.started_at = time.monotonic()
        self.active_pose = "home"
        self.completed = True
        self.get_logger().info("Ready; publish semantic poses on /geekseek/fake_robot/target")

    @staticmethod
    def _radians(values: tuple[int, ...]) -> list[float]:
        return [math.radians(value) for value in values]

    def on_target(self, message: String) -> None:
        if message.data not in POSES:
            self.get_logger().warning(f"Unknown pose: {message.data}")
            return
        self.start = list(self.current)
        self.target = self._radians(POSES[message.data])
        self.started_at = time.monotonic()
        self.active_pose = message.data
        self.completed = False
        self.status_publisher.publish(String(data=f"moving:{self.active_pose}"))

    def tick(self) -> None:
        elapsed = time.monotonic() - self.started_at
        ratio = min(1.0, elapsed / max(self.move_seconds, 0.001))
        smooth = ratio * ratio * (3.0 - 2.0 * ratio)
        self.current = [
            start + (target - start) * smooth for start, target in zip(self.start, self.target)
        ]
        message = JointState()
        message.header.stamp = self.get_clock().now().to_msg()
        message.name = JOINT_NAMES
        message.position = self.current
        self.publisher.publish(message)

        if ratio >= 1.0 and not self.completed:
            self.completed = True
            self.status_publisher.publish(String(data=f"completed:{self.active_pose}"))


def main(args=None) -> None:
    rclpy.init(args=args)
    node = FakeRobotNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
