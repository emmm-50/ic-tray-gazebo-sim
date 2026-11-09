"""Launch the mobile workcell and its ROS bridge without building a package."""

import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

from launch import LaunchDescription, LaunchService
from launch.actions import EmitEvent, ExecuteProcess, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch_ros.actions import Node

from world import write_world


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runtime_dir", type=Path)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--integration", action="store_true")
    args = parser.parse_args()

    with TemporaryDirectory(prefix="run-", dir=args.runtime_dir) as run_dir:
        world = Path(run_dir) / "mobile_workcell.sdf"
        if args.integration:
            from integration import build
            from ic_tray_sim.launch_support import suction_bridge, arm_controllers, tray_after_controllers
            world, xml, tray_sdf, tray_xyz = build(run_dir)
        else:
            write_world(world)
        gz_args = ["gz", "sim", "-r", "-v", "3"]
        if args.headless:
            gz_args.extend(("-s", "--headless-rendering"))
        gazebo = ExecuteProcess(cmd=[*gz_args, str(world)], output="screen")

        service = LaunchService()
        actions = [
            RegisterEventHandler(
                OnProcessExit(
                    target_action=gazebo,
                    on_exit=[EmitEvent(event=Shutdown(reason="Gazebo closed"))],
                )
            ),
            gazebo,
            Node(
                package="ros_gz_bridge",
                executable="parameter_bridge",
                name="mobile_workcell_bridge",
                parameters=[
                    {"config_file": str(Path(__file__).with_name("bridge.yaml").resolve())}
                ],
                output="screen",
            ),
            Node(
                package="tf2_ros",
                executable="static_transform_publisher",
                name="mobile_laser_transform",
                arguments=[
                    "--x", "0.32", "--z", "0.34",
                    "--frame-id", "base_link", "--child-frame-id", "laser",
                ],
                output="screen",
            ),
        ]
        if args.integration:
            publisher = Node(
                package="robot_state_publisher", executable="robot_state_publisher",
                parameters=[{"robot_description": xml, "use_sim_time": True}],
                output="screen",
            )
            suction = suction_bridge()
            controllers = arm_controllers()
            tray_handler = tray_after_controllers(controllers, tray_sdf, tray_xyz)
            actions.extend([
                publisher, suction,
                tray_handler,
                controllers,
            ])
        service.include_launch_description(LaunchDescription(actions))
        return service.run()


if __name__ == "__main__":
    raise SystemExit(main())
