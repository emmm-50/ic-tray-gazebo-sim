# 本机 SLAM 备用方案

本阶段验收在线建图和地图保存。仿真与键盘沿用项目 Conda 环境，SLAM 与地图保存器使用独立解包的系统 Jazzy 二进制。测试使用了虚拟终端输入键盘指令。

## 准备依赖

需要本机已有 `/opt/ros/jazzy`、APT 包索引和网络。以下命令仅下载并解包缺失的运行包，不执行系统安装。APT 解析结果随系统现有包状态变化；`/tmp` 重启后可能被清理。

```bash
mkdir -p /tmp/ic-tray-slam-native/debs
cd /tmp/ic-tray-slam-native/debs
apt-get download $(apt-get -s install --no-install-recommends ros-jazzy-slam-toolbox ros-jazzy-nav2-map-server | awk '/^Inst/ && $2 !~ /-dev(-compat)?$/ {print $2}')
for deb in *.deb; do dpkg-deb -x "$deb" ../root || exit; done
```

## 启动

从仓库根目录，在每个终端设置相同的域和 Gazebo 分区：

```bash
export IC_TRAY_MOBILE_ROS_DOMAIN_ID=181
export IC_TRAY_MOBILE_GZ_PARTITION=ic_tray_slam_fallback
```

终端 1：`bash mobile_workcell/run.sh sim`（无界面可追加 `--headless`）。终端 2：`bash slam_fallback/run.sh mapping`。终端 3：`bash mobile_workcell/run.sh keyboard`，按 S 倒车、A/D 转向，空格停车，Q 退出。保持建图运行并缓慢移动扫描环境。测试时通过虚拟终端约每秒输入一次 S，持续倒车约 1 米，地图从 20 × 101 扩展到 42 × 101；也可长按或连续点按，以实际位移为准。

终端 4 保存地图：

```bash
mkdir -p log/slam_fallback/maps
bash slam_fallback/run.sh save "$PWD/log/slam_fallback/maps/workcell"
```

生成 `workcell.pgm` 和 `workcell.yaml`。等待 `/map` 出现后再保存。检查接口：

```bash
bash slam_fallback/run.sh ros topic echo /map nav_msgs/msg/OccupancyGrid --qos-durability transient_local --once --field info
bash slam_fallback/run.sh ros run tf2_ros tf2_echo map laser
```

TF 链为 `map → odom → base_link → laser`。地图质量取决于扫描路径和里程计；仿真雷达为前向 180°。可用 `IC_TRAY_SLAM_ROOT` 指向其他解包根目录。停止所有进程后可删除 `/tmp/ic-tray-slam-native` 清理临时依赖。
