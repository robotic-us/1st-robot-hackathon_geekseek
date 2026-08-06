from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
import os


def generate_launch_description() -> LaunchDescription:
    package_dir = get_package_share_directory("geekseek_fake_robot")
    xacro_file = os.path.join(package_dir, "urdf", "geekseek_fake_robot.urdf.xacro")
    rviz_file = os.path.join(package_dir, "rviz", "geekseek_fake_robot.rviz")
    robot_description = ParameterValue(Command(["xacro ", xacro_file]), value_type=str)

    return LaunchDescription(
        [
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                parameters=[{"robot_description": robot_description}],
            ),
            Node(
                package="geekseek_fake_robot",
                executable="fake_robot_node",
                output="screen",
            ),
            Node(
                package="rviz2",
                executable="rviz2",
                arguments=["-d", rviz_file],
                output="screen",
            ),
        ]
    )
