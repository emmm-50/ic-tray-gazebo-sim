"""Shared arm control and suction launch actions for fixed and mobile scenes."""
from launch.actions import RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch_ros.actions import Node


def suction_bridge(include_clock=False):
    topics = [
        '/suction/attach@std_msgs/msg/Empty]gz.msgs.Empty',
        '/suction/detach@std_msgs/msg/Empty]gz.msgs.Empty',
        '/suction/state@std_msgs/msg/String[gz.msgs.StringMsg',
    ]
    if include_clock:
        topics.insert(0, '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock')
    return Node(
        package='ros_gz_bridge', executable='parameter_bridge', output='screen',
        parameters=[{
            'qos_overrides./suction/state.publisher.durability': 'transient_local',
            'qos_overrides./suction/state.publisher.depth': 1,
        }], arguments=topics,
    )


def arm_controllers():
    return Node(
        package='controller_manager', executable='spawner', output='screen',
        arguments=['joint_state_broadcaster', 'arm_controller', '--controller-manager-timeout', '120'],
    )


def tray_after_controllers(controllers, sdf, xyz, yaw=None):
    args = ['-string', sdf, '-name', 'tray', '-x', str(xyz[0]),
            '-y', str(xyz[1]), '-z', str(xyz[2])]
    if yaw is not None:
        args += ['-Y', str(yaw)]
    tray = Node(package='ros_gz_sim', executable='create', arguments=args, output='screen')
    return RegisterEventHandler(OnProcessExit(
        target_action=controllers,
        on_exit=lambda event, _: [tray] if event.returncode == 0 else [],
    ))
