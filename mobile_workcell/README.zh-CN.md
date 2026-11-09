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
