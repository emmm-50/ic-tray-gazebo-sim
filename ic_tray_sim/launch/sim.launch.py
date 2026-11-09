from pathlib import Path
import os
import tempfile
import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ic_tray_sim.launch_support import suction_bridge, arm_controllers, tray_after_controllers
from ic_tray_sim.scene import B1_YAW, robot_xml, tray_sdf, tray_position, world


def start(context):
    share = Path(get_package_share_directory('ic_tray_sim'))
    description = Path(get_package_share_directory('prrr_arm_description'))
    config_path = LaunchConfiguration('task_config').perform(context)
    with open(config_path, encoding='utf-8') as f:
        cfg = yaml.safe_load(f)
    xml = robot_xml(description, share / 'config/controllers.yaml', cfg)
    # Gazebo consumes a file; the generated world is private to this launch process.
    world_file = tempfile.NamedTemporaryFile(mode='w', prefix='ic_tray_', suffix='.sdf', delete=False, encoding='utf-8')
    with world_file:
        world_file.write(world(cfg))
    headless = LaunchConfiguration('gui').perform(context).lower() == 'false'
    gui_config = Path(os.environ['CONDA_PREFIX']) / 'share/gz/gz-sim8/gui/gui.config'
    gz_args = '-r ' + ('-s ' if headless else '--gui-config ' + str(gui_config) + ' ') + world_file.name
    gz = IncludeLaunchDescription(PythonLaunchDescriptionSource(str(Path(get_package_share_directory('ros_gz_sim')) / 'launch/gz_sim.launch.py')), launch_arguments={'gz_args': gz_args, 'on_exit_shutdown': 'true'}.items())
    publisher = Node(package='robot_state_publisher', executable='robot_state_publisher', output='screen', parameters=[{'robot_description': xml, 'use_sim_time': True}])
    bridge = suction_bridge(include_clock=True)
    spawn = Node(package='ros_gz_sim', executable='create', arguments=['-topic', '/robot_description', '-name', 'prrr_arm'], output='screen')
    controllers = arm_controllers()
    tray_xyz = tray_position(cfg)
    # The A carry tray is rotated 180 degrees relative to the wrist.
    tray_handler = tray_after_controllers(
        controllers, tray_sdf(cfg), tray_xyz,
        -B1_YAW if cfg.get('mode') == 'b1_place' else 0.0,
    )
    return [gz, publisher, bridge,
            RegisterEventHandler(OnProcessExit(target_action=spawn, on_exit=lambda event, _: [controllers] if event.returncode == 0 else [])),
            tray_handler,
            spawn]


def generate_launch_description():
    config = str(Path(get_package_share_directory('ic_tray_sim')) / 'config/task.yaml')
    return LaunchDescription([DeclareLaunchArgument('gui', default_value='true'), DeclareLaunchArgument('task_config', default_value=config), OpaqueFunction(function=start)])
