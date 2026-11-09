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
    args = parser.parse_args()

    with TemporaryDirectory(prefix="run-", dir=args.runtime_dir) as run_dir:
        world = Path(run_dir) / "mobile_workcell.sdf"
        write_world(world)
        gz_args = ["gz", "sim", "-r", "-v", "3"]
        if args.headless:
            gz_args.extend(("-s", "--headless-rendering"))
        gazebo = ExecuteProcess(cmd=[*gz_args, str(world)], output="screen")

        service = LaunchService()
        service.include_launch_description(
            LaunchDescription(
                [
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
            )
        )
        return service.run()


if __name__ == "__main__":
    raise SystemExit(main())
