#!/usr/bin/env bash
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
root="${IC_TRAY_SLAM_ROOT:-/tmp/ic-tray-slam-native/root}"
unset AMENT_PREFIX_PATH CMAKE_PREFIX_PATH COLCON_PREFIX_PATH LD_LIBRARY_PATH PYTHONPATH ROS_DISTRO ROS_VERSION ROS_PYTHON_VERSION
set +u
source /opt/ros/jazzy/setup.bash
set -u
prefix="$root/opt/ros/jazzy"
export AMENT_PREFIX_PATH="$prefix:$AMENT_PREFIX_PATH"
export LD_LIBRARY_PATH="$prefix/lib:$root/usr/lib:$root/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH:-}"
export PYTHONPATH="$prefix/lib/python3.12/site-packages:${PYTHONPATH:-}"
mkdir -p "$here/../log/slam_fallback"
export ROS_LOG_DIR="$here/../log/slam_fallback"
export ROS_DOMAIN_ID="${IC_TRAY_MOBILE_ROS_DOMAIN_ID:-181}"
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export GZ_PARTITION="${IC_TRAY_MOBILE_GZ_PARTITION:-ic_tray_slam_fallback}"
case "${1:-}" in
  mapping) exec ros2 launch slam_toolbox online_async_launch.py slam_params_file:="$here/mapper.yaml" use_sim_time:=true ;;
  save) shift; exec ros2 run nav2_map_server map_saver_cli -f "${1:?map output path required}" --ros-args -p use_sim_time:=true -p save_map_timeout:=10.0 ;;
  ros) shift; exec ros2 "$@" ;;
  *) echo "Usage: $0 {mapping|save PATH|ros ARGS...}" >&2; exit 2 ;;
esac
