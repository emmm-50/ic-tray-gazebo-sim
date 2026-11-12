#!/usr/bin/env bash
set -euo pipefail

mobile_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
project_dir="$(dirname -- "$mobile_dir")"
runtime_dir="${IC_TRAY_MOBILE_RUNTIME_DIR:-$project_dir/log/mobile_workcell}"
default_domain=180
default_partition=ic_tray_mobile_workcell

case "${1:-}" in
  demo)
    shift
    exec bash "$mobile_dir/demo.sh" "$@"
    ;;
  sim)
    shift
    if [[ " $* " == *" --integration "* ]]; then
      default_domain=182
      default_partition=ic_tray_integration
    fi
    entry=(python "$mobile_dir/sim.py" "$runtime_dir" "$@")
    ;;
  keyboard|xbox)
    entry=(python "$mobile_dir/teleop.py" "$@")
    ;;
  ros)
    shift
    entry=(ros2 "$@")
    ;;
  *)
    printf 'Usage: bash %s {demo [--headless]|sim [--headless]|keyboard|xbox|ros <ros2 arguments>}\n' "${BASH_SOURCE[0]}" >&2
    exit 2
    ;;
esac

mkdir -p "$runtime_dir/"{fuel,gz,ros,cache,config}
exec bash "$project_dir/tools/run_isolated.sh" env \
  ROS_DOMAIN_ID="${IC_TRAY_MOBILE_ROS_DOMAIN_ID:-$default_domain}" \
  ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST \
  GZ_PARTITION="${IC_TRAY_MOBILE_GZ_PARTITION:-$default_partition}" \
  GZ_IP=127.0.0.1 QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-xcb}" \
  GZ_SIM_RESOURCE_PATH="$project_dir/artifacts/asset_sourcing/preview/models:$project_dir" \
  GZ_FUEL_CACHE_PATH="$runtime_dir/fuel" GZ_LOG_PATH="$runtime_dir/gz" \
  ROS_HOME="$runtime_dir/ros" ROS_LOG_DIR="$runtime_dir/ros" \
  XDG_CACHE_HOME="$runtime_dir/cache" XDG_CONFIG_HOME="$runtime_dir/config" \
  "${entry[@]}"
