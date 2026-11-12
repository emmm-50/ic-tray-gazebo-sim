# 移动工位模拟遥控

移动入口复用仓库现有分站工位、障碍和收拢臂视觉，生成带差速底盘的独立世界。小车从 A 位启动，车头朝传送带。车载机械臂显示为跟随底盘的固定收拢模型。

本入口使用项目已有 Conda 环境，无需构建 ROS 包。默认 ROS 域为 **180**，Gazebo 分区为 `ic_tray_mobile_workcell`，与固定工位和 A 位取盘仿真分开。场景启动和控制在同一台电脑运行。若改用 `IC_TRAY_MOBILE_ROS_DOMAIN_ID` 或 `IC_TRAY_MOBILE_GZ_PARTITION`，各终端使用相同设置。

## 启动和遥控

终端 1，从仓库根目录启动 Gazebo、ROS 桥和雷达静态 TF。

```bash
bash mobile_workcell/run.sh sim
```

等 Gazebo 场景显示后，在终端 2 从仓库根目录启动键盘遥控。

```bash
bash mobile_workcell/run.sh keyboard
```

焦点保持在遥控终端。W/S 前进和倒车，A/D 原地左右转，空格停车，Q 退出。键盘是短点动，约 0.3 秒没有收到按键输入会发零速；长按效果取决于桌面按键重复设置。小车初始面向取盘台，可先按 S 倒出。默认线速度 0.2 m/s、角速度 0.5 rad/s，可用 `--linear` 和 `--angular` 调整。

也可在系统识别 Xbox 兼容手柄后，用下面的命令代替键盘遥控。同一时间启动一个速度指令来源。

```bash
bash mobile_workcell/run.sh xbox
```

按住 LB 使能，左摇杆上下控制前后，右摇杆左右控制转向，松开 LB 发零速。Ctrl+C 退出。如连接了多个 SDL2 手柄，可用 `xbox --device N` 指定索引。正常退出会重复发送零速。直接在 ROS 发布速度时，停止也应发零速。Gazebo DiffDrive 会维持最近一次收到的速度。

## 给建图同学的接口

| ROS 2 接口 | 消息 / 坐标 |
| --- | --- |
| `/cmd_vel` | 输入 `geometry_msgs/msg/Twist`，使用 `linear.x` 与 `angular.z` |
| `/scan` | 输出 `sensor_msgs/msg/LaserScan`，帧 `laser`，前向 180°，361 束，10 Hz |
| `/odom` | 输出 `nav_msgs/msg/Odometry`，轮式里程计，父帧 `odom`，子帧 `base_link` |
| `/tf` | 动态 `odom → base_link` |
| `/tf_static` | `base_link → laser`，位置 (0.32, 0, 0.34) m，零旋转 |
| `/clock` | Gazebo 仿真时钟，建图节点用 `use_sim_time:=true` |

用同一入口检查 ROS 话题，确保落在对应 ROS 域内。

```bash
bash mobile_workcell/run.sh ros topic list --no-daemon --spin-time 2
bash mobile_workcell/run.sh ros topic echo /scan --once --qos-reliability best_effort
bash mobile_workcell/run.sh ros topic echo /odom --once
bash mobile_workcell/run.sh ros run tf2_ros tf2_echo odom laser
```

`sim --headless` 可在无界面环境启动并保留雷达。底盘质量、摩擦和轮式里程计为仿真参数。SLAM 建图与导航由负责同学接入。

本机 Gazebo Harmonic 8.10.0 已实测键盘倒车、转向、空格停车及 Q 退出停车，并按雷达采样时间查询到 `odom → laser`。Xbox 的摇杆和 LB 逻辑通过 SDL2 虚拟设备验证，实体手柄待实测。

## 移动取盘与 B1 放盘集成

集成模式在差速底盘上加载可动机械臂和一个动态全尺寸托盘。先构建 `ic_tray_sim` 与 `prrr_arm_description`，然后在各终端设置同一隔离域与分区：

```bash
export IC_TRAY_MOBILE_ROS_DOMAIN_ID=182
export IC_TRAY_MOBILE_GZ_PARTITION=ic_tray_integration
```

终端 1 启动场景（无界面可加 `--headless`）：

```bash
bash mobile_workcell/run.sh sim --integration
```

等待控制器加载和托盘生成，在终端 2 执行 A 位取盘、抬升和收拢：

```bash
bash mobile_workcell/run.sh ros run ic_tray_sim pick_place --ros-args \
  -p task_config:="$PWD/ic_tray_sim/config/a_pickup.yaml"
```

之后使用上面的 `keyboard` 命令倒出 A 位，再向东、向北绕行到 B1，停在底盘约 `(1.49, 1.51)` m、车头朝北的位置。车辆停稳且托盘保持吸附后，可运行固定 B1 上层第 3 槽轨迹：

```bash
bash mobile_workcell/run.sh ros run ic_tray_sim pick_place --ros-args \
  -p task_config:="$PWD/ic_tray_sim/config/b1_place.yaml"
```

默认命令选择上层第 3 槽。选择第 1、2、4 槽时，将 `task_config` 换成对应的 `ic_tray_sim/config/b1_slot1.yaml`、`b1_slot2.yaml` 或 `b1_slot4.yaml`，按其中的 `dock_xy` 停车，车头朝 +Y。自主导航的停车验收见下文。停车修正后的路径仍需留出机械臂与货架和邻盘的净距。

A 位收拢使用负肘构型。B1 先展开到中间姿态，再从工具坐标 `x=0.23 m` 的高位沿中心线插入，释放后抬升、退回并收拢空臂。第 3 槽曾在第 2、4 槽均有全尺寸托盘的场景中完成放盘。

对记录的仿真位姿逐帧检查，未发现非相邻机械臂部件之间、机械臂与托盘或工位之间的相交。托盘与支撑面接触时有微小几何重叠。检查结论限于记录的仿真位姿。

这条轨迹假定上述精确停车位姿；停车偏差可能使托盘碰撞或偏离槽位。测试使用一次实测停车位姿修正：将名义工具目标从名义底盘和安装位姿转换到世界坐标，再用测得的底盘位姿转换回机械臂坐标，保留目标高度和插入路径。`log/integration/check_drive.py` 展示计算方法；它依赖测试采集的 Gazebo 位姿，不能替代实际定位。

验证回放 `log/integration/replay_drive.py` 通过 PTY 向同一个键盘遥控程序注入按键，并使用 Gazebo 真值决定何时切换按键，仅用于仿真验证，不是自动导航或自动停靠功能。运行数据和检查结果保存在 `log/integration/`，可与原有 `/cmd_vel`、`/scan`、`/odom`、`/tf`、`/tf_static` 和 `/clock` 接口并行使用。

### 复现验证记录

以下命令在仓库根目录执行，每次创建新目录。它们需要上面的集成环境变量和已构建的包。先在一个终端启动场景：

```bash
export IC_TRAY_MOBILE_ROS_DOMAIN_ID=182 IC_TRAY_MOBILE_GZ_PARTITION=ic_tray_integration
bash mobile_workcell/run.sh sim --integration --headless
```

控制器和托盘生成后，在另一个终端记录位姿并执行抓取、键盘测试与放盘：

```bash
export IC_TRAY_MOBILE_ROS_DOMAIN_ID=182 IC_TRAY_MOBILE_GZ_PARTITION=ic_tray_integration
set -o pipefail
mkdir -p log/integration
run_dir="$(mktemp -d "$PWD/log/integration/run-XXXXXX")"
bash tools/run_isolated.sh env GZ_PARTITION=ic_tray_integration GZ_IP=127.0.0.1 \
  gz topic -e -t /world/ic_tray_mobile_workcell/dynamic_pose/info > "$run_dir/poses.txt" &
pose_pid=$!
bash mobile_workcell/run.sh ros run ic_tray_sim pick_place --ros-args \
  -p task_config:="$PWD/ic_tray_sim/config/a_pickup.yaml" 2>&1 | tee "$run_dir/pickup.log"
bash tools/run_isolated.sh env ROS_DOMAIN_ID=182 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST \
  GZ_PARTITION=ic_tray_integration GZ_IP=127.0.0.1 \
  python log/integration/replay_drive.py --output "$run_dir/drive.csv" 2>&1 | tee "$run_dir/drive.log"
bash tools/run_isolated.sh python log/integration/check_drive.py "$run_dir/drive.csv" "$run_dir"
bash mobile_workcell/run.sh ros run ic_tray_sim pick_place --ros-args \
  -p task_config:="$run_dir/b1-corrected.yaml" 2>&1 | tee "$run_dir/place.log"
```

放盘退臂后让仿真继续至少 5 秒，再结束采集并检查结果：

```bash
kill -INT "$pose_pid"
wait "$pose_pid" || true
bash tools/run_isolated.sh python log/integration/check_poses.py \
  "$run_dir/poses.txt" "$run_dir/drive.csv" "$run_dir/pose-summary.json"
```

`pose-summary.json` 将相对底盘的腕部位姿以完整四元数变换到世界坐标后，再计算腕部与托盘的相对位姿。槽位检查分别使用横向标线和货架板前后边缘；吸附是固定关节近似。测试用的采集与检查脚本及运行记录保存在本工作区忽略的 `log/integration/`，不会随 Git 提交。

### 同时运行 SLAM

先按 [SLAM 备用方案](../slam_fallback/README.zh-CN.md)准备原生 Jazzy 依赖。集成仿真启动后，在另一个终端使用相同的 `IC_TRAY_MOBILE_ROS_DOMAIN_ID=182` 和 `IC_TRAY_MOBILE_GZ_PARTITION=ic_tray_integration` 启动：

```bash
bash slam_fallback/run.sh mapping
```

保持建图运行，按上面的 A 取盘、键盘移动和 B1 放盘步骤操作。验证时可在建立好 `run_dir` 后另行记录地图更新和部分真实扫描时间对应的 TF 链：

```bash
bash tools/run_isolated.sh env ROS_DOMAIN_ID=182 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST \
  GZ_PARTITION=ic_tray_integration GZ_IP=127.0.0.1 \
  python log/integration/slam_capture.py "$run_dir/slam-evidence.json" &
slam_capture_pid=$!
```

到 B1 后保存地图；结束记录后停止采集：

```bash
bash slam_fallback/run.sh save "$run_dir/map"
kill -INT "$slam_capture_pid"
wait "$slam_capture_pid" || true
```

本次同跑的原始数据在 `log/integration/slam-corun/`。键盘路线由 PTY 输入驱动并使用仿真真值切换按键，SLAM 只负责建图；这不是导航或自动停靠测试。

### SLAM 自主导航到 B1 并修正放盘

本机固定场景下，导航将出发时 SLAM Toolbox 发布的 `/map` 占据格叠加到 SDF 的二维障碍图。A 位起点取自底盘模型，倒车净空用合并后的障碍检查，驶出后用按底盘外形膨胀的障碍图做 A* 规划。行车用 `workcell → map → odom → base_link` 闭环跟踪。激光配准从同一份 SDF 几何中选取激光高度处的截面，在检测到明显漂移时更新 `workcell → map`。

以下命令从联调工作树根目录运行。先按上文构建并启动集成场景与 SLAM。对齐节点和导航进程使用原生 Jazzy 的 Python 环境，对齐还需要 NumPy 和 SciPy。在对应的终端使用和仿真相同的 ROS 域和 Gazebo 分区。

```bash
export IC_TRAY_MOBILE_ROS_DOMAIN_ID=182 IC_TRAY_MOBILE_GZ_PARTITION=ic_tray_integration
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID="$IC_TRAY_MOBILE_ROS_DOMAIN_ID" ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
/usr/bin/python3 mobile_workcell/align_slam.py
```

等待激光对齐日志出现，再在另一个终端取盘、导航和放盘。

```bash
export IC_TRAY_MOBILE_ROS_DOMAIN_ID=182 IC_TRAY_MOBILE_GZ_PARTITION=ic_tray_integration
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID="$IC_TRAY_MOBILE_ROS_DOMAIN_ID" ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
mkdir -p "$PWD/log/integration"
run_dir="$(mktemp -d "$PWD/log/integration/slam-gui-XXXXXX")"
bash mobile_workcell/run.sh ros run ic_tray_sim pick_place --ros-args \
  -p task_config:="$PWD/ic_tray_sim/config/a_pickup.yaml"
/usr/bin/python3 mobile_workcell/navigate.py \
  --sdf artifacts/asset_sourcing/layout/slam/slam_workcell.sdf \
  --csv "$run_dir/drive.csv" --output "$run_dir/stopped.json"
bash tools/run_isolated.sh python mobile_workcell/correct_b1_pose.py \
  "$run_dir/stopped.json" "$run_dir/b1-corrected.yaml"
bash mobile_workcell/run.sh ros run ic_tray_sim pick_place --ros-args \
  -p task_config:="$run_dir/b1-corrected.yaml"
```

导航和停车修正默认使用 B1 上层第 3 槽的 `b1_place.yaml`。指定槽位配置时，给 `navigate.py` 和 `correct_b1_pose.py` 传入同一个 `--config`。停车后，用测得的底盘位置和朝向、共享臂座偏移，把名义工具目标和整段进槽路径换算到当前臂座。规划依赖固定的工位几何和出发时的地图快照，仅覆盖此仿真场景。Gazebo 真值用于验收。

#### B1 上层槽位停车验收

上层第 1–4 槽各自配置 `dock_tolerance`。它表示相对该槽名义停车位姿的工作区坐标偏差，当前仿真验收范围为 x、y 各 ±5 mm，偏航 ±0.01 rad，来自相邻槽放有全尺寸托盘的离线轨迹采样。首停默认对准范围中心。

首停越界时，导航用同一份合并地图检查从当前位置到区间中心的车体净空。净空通过后低速转向、短距直行、回正并重新停稳。导航在验收通过后写出本次 `stopped.json`，停车修正命令也按同一范围核对输入。用新的运行目录依次执行导航、修正和放盘，前一步成功后再执行下一步。

在 Gazebo 复现第 2 槽的偏停时，将导航和修正的 `--config` 指向 `ic_tray_sim/config/b1_slot2.yaml`，给 `navigate.py` 加 `--initial-offset 0.025 0.010 -0.015459`，单位为米、米、弧度。该偏差加在第一次导航目标上，实际首停与重停位姿见导航日志。

#### 前进途中遇障停车

导航正向驱动时用实时 `/scan` 检查车头前方，检测距离随指令速度变化，最大为 0.25 m，横向覆盖车宽及两侧各 30 mm 余量。检测到障碍或扫描过期时发零速，收到新鲜且通道清空的扫描后沿当前路线继续。A 位倒车仍使用出发时合并地图的净空检查。
