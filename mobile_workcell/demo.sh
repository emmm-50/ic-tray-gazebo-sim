#!/usr/bin/env bash
# Run the complete A pickup, SLAM navigation and B1 placement demonstration.
set -euo pipefail

mobile_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
project_dir="$(dirname -- "$mobile_dir")"
cd "$project_dir"

headless=false
case "${1:-}" in
  '') ;;
  --headless) headless=true; shift ;;
  -h|--help)
    printf 'Usage: bash mobile_workcell/run.sh demo [--headless]\n'
    exit 0 ;;
  *) printf 'Usage: bash mobile_workcell/run.sh demo [--headless]\n' >&2; exit 2 ;;
esac
if (($#)); then
  printf 'Usage: bash mobile_workcell/run.sh demo [--headless]\n' >&2
  exit 2
fi

mkdir -p "$project_dir/log/demo"
run_dir="$(mktemp -d "$project_dir/log/demo/demo-XXXXXX")"
printf '演示日志：%s\n' "$run_dir"
export IC_TRAY_MOBILE_ROS_DOMAIN_ID="${IC_TRAY_MOBILE_ROS_DOMAIN_ID:-197}"
export IC_TRAY_MOBILE_GZ_PARTITION="${IC_TRAY_MOBILE_GZ_PARTITION:-ic_tray_demo_197}"
export IC_TRAY_MOBILE_RUNTIME_DIR="$run_dir/mobile_runtime"
export ROS_LOG_DIR="$run_dir/native_ros"
# Native Jazzy's Gazebo paths must not leak into the Conda simulator.
unset GZ_CONFIG_PATH

pids=()
start() {
  local log_file="$1"
  shift
  setsid "$@" </dev/null >"$log_file" 2>&1 &
  pids+=("$!")
}
cleanup() {
  local pid
  for pid in "${pids[@]}"; do
    kill -TERM -- "-$pid" 2>/dev/null || true
  done
  for pid in "${pids[@]}"; do
    wait "$pid" 2>/dev/null || true
  done
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

printf '构建仿真包…\n'
bash tools/run_isolated.sh colcon --log-base "$run_dir/colcon" build \
  --base-paths prrr_arm_description ic_tray_sim --build-base build/conda \
  --install-base install/conda |& tee "$run_dir/build.log"

sim_args=(sim --integration)
if "$headless"; then sim_args+=(--headless); fi
start "$run_dir/sim.log" bash mobile_workcell/run.sh "${sim_args[@]}"
sim_pid="${pids[-1]}"
start "$run_dir/slam.log" bash slam_fallback/run.sh mapping
slam_pid="${pids[-1]}"
start "$run_dir/align.log" bash slam_fallback/run.sh python "$mobile_dir/align_slam.py"
align_pid="${pids[-1]}"

printf '等待托盘生成与 SLAM 配准…\n'
# The arm and chassis are in the world SDF; the only create action spawns the tray.
deadline=$((SECONDS + 90))
until grep -Fq 'Entity creation successful' "$run_dir/sim.log" 2>/dev/null && \
      grep -Fq 'workcell_base=' "$run_dir/align.log" 2>/dev/null; do
  for pid in "$sim_pid" "$slam_pid" "$align_pid"; do
    if ! kill -0 "$pid" 2>/dev/null; then
      printf '演示组件提前退出，请检查 %s\n' "$run_dir" >&2
      exit 1
    fi
  done
  if ((SECONDS >= deadline)); then
    printf '等待仿真或配准超时，请检查 %s\n' "$run_dir" >&2
    exit 1
  fi
  sleep 1
done

printf 'A 位取盘…\n'
bash mobile_workcell/run.sh ros run ic_tray_sim pick_place --ros-args \
  -p task_config:="$project_dir/ic_tray_sim/config/a_pickup.yaml" |& tee "$run_dir/pickup.log"
printf '导航至 B1…\n'
b1_config="$project_dir/ic_tray_sim/config/b1_place.yaml"
bash slam_fallback/run.sh python "$mobile_dir/navigate.py" \
  --sdf "$project_dir/artifacts/asset_sourcing/layout/slam/slam_workcell.sdf" \
  --config "$b1_config" \
  --csv "$run_dir/drive.csv" --output "$run_dir/stopped.json" |& tee "$run_dir/navigate.log"
printf '修正停车位姿并放盘…\n'
bash tools/run_isolated.sh python "$mobile_dir/correct_b1_pose.py" \
  "$run_dir/stopped.json" "$run_dir/b1-corrected.yaml" \
  --config "$b1_config" |& tee "$run_dir/correction.log"
bash mobile_workcell/run.sh ros run ic_tray_sim pick_place --ros-args \
  -p task_config:="$run_dir/b1-corrected.yaml" |& tee "$run_dir/place.log"

printf '演示完成。日志：%s\n' "$run_dir"
if ! "$headless"; then
  bash tools/run_isolated.sh env GZ_PARTITION="$IC_TRAY_MOBILE_GZ_PARTITION" GZ_IP=127.0.0.1 \
    gz service -s /world/ic_tray_mobile_workcell/control --reqtype gz.msgs.WorldControl \
    --reptype gz.msgs.Boolean --timeout 4000 --req 'pause: true' > "$run_dir/pause.log"
  if ! grep -Fq 'data: true' "$run_dir/pause.log"; then
    printf '无法暂停仿真，请检查 %s/pause.log\n' "$run_dir" >&2
    exit 1
  fi
  printf '仿真已暂停，关闭 Gazebo 窗口或按 Ctrl+C 结束。\n'
  wait "$sim_pid"
fi
