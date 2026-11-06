#!/usr/bin/env bash
set -e
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
unset AMENT_PREFIX_PATH CMAKE_PREFIX_PATH COLCON_PREFIX_PATH LD_LIBRARY_PATH PYTHONPATH ROS_DISTRO ROS_VERSION ROS_PYTHON_VERSION
CONDA_ROOT="${IC_TRAY_CONDA_ROOT:-$HOME/miniforge3}"
ENV_PREFIX="${IC_TRAY_ENV_PREFIX:-$CONDA_ROOT/envs/ic_tray_jazzy}"
source "$CONDA_ROOT/etc/profile.d/conda.sh"
conda activate "$ENV_PREFIX"
export ROS_DOMAIN_ID=73 GZ_PARTITION=ic_tray_course_01a1aaea
export ROS_HOME="$PROJECT_DIR/log/conda/ros" ROS_LOG_DIR="$PROJECT_DIR/log/conda/ros/log" GZ_LOG_PATH="$PROJECT_DIR/log/conda/gz"
export XDG_CACHE_HOME="$PROJECT_DIR/log/conda/xdg/cache" XDG_CONFIG_HOME="$PROJECT_DIR/log/conda/xdg/config"
mkdir -p "$XDG_CACHE_HOME" "$XDG_CONFIG_HOME"
if [ -f "$PROJECT_DIR/install/conda/setup.bash" ]; then
  source "$PROJECT_DIR/install/conda/setup.bash"
fi
exec env -u HOME "$@"
