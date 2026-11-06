"""ROS 2: show the complete arm and initialize the four joints to the CAD pose."""
import json
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    share = Path(get_package_share_directory('prrr_arm_description'))
    model = share / 'urdf' / 'prrr_arm.urdf'
    pose = json.loads((share / 'config' / 'cad_pose.json').read_text(encoding='utf-8'))
    gui = LaunchConfiguration('gui')
    zeros = {'zeros.' + name: float(value) for name, value in pose.items()}
    return LaunchDescription([
        DeclareLaunchArgument('gui', default_value='true'),
        DeclareLaunchArgument('rviz', default_value='true'),
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             parameters=[{'robot_description': ParameterValue(model.read_text(encoding='utf-8'), value_type=str),
                          'use_sim_time': ParameterValue(LaunchConfiguration('use_sim_time'), value_type=bool)}],
             output='screen'),
        Node(package='joint_state_publisher_gui', executable='joint_state_publisher_gui',
             name='joint_state_publisher', arguments=[str(model)], parameters=[zeros],
             condition=IfCondition(gui), output='screen'),
        Node(package='joint_state_publisher', executable='joint_state_publisher',
             name='joint_state_publisher', arguments=[str(model)], parameters=[zeros],
             condition=UnlessCondition(gui), output='screen'),
        Node(package='rviz2', executable='rviz2',
             arguments=['-d', str(share / 'config' / 'display_ros2.rviz')],
             condition=IfCondition(LaunchConfiguration('rviz')), output='screen'),
    ])
