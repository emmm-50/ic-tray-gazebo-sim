# 完整机械臂 ROS 模型

这是一个完整机械臂模型，主文件为 `urdf/prrr_arm.urdf`，附带 5 个按运动连杆合并的 STL。没有单独的螺钉、吸盘或其他零件文件。5 个合并网格共同组成完整机械臂，保留全部 138 个源零件实例的外形。导入或传输时请保留整个 `prrr_arm_description` 文件夹；URDF 通过 `package://` 读取这些必要网格。

来源：完善版的 `模型/机械臂加工总装.SLDASM`，当前配置“输送线取盘”。该文件比交付目录的旧总装保存时间更晚，引用相同的完善版零件。原始 SolidWorks 文件只读导出，没有改写。

## ROS 2 导入

已安装 ROS 2 的 Linux 电脑上，先加载本机 ROS 环境，将此文件夹放在 `~/ros2_ws/src/` 内，然后执行：

```bash
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --packages-select prrr_arm_description
source install/setup.bash
ros2 launch prrr_arm_description display.launch.py
```

启动后在 RViz2 中显示整个机械臂，并弹出四关节调节窗口；初始值读取当前 CAD 姿态。无图形界面测试可执行 `ros2 launch prrr_arm_description display.launch.py gui:=false rviz:=false`。

## ROS 1 导入

在已加载 ROS 1 Noetic 环境的电脑上，将此文件夹放在 `~/catkin_ws/src/` 内：

```bash
cd ~/catkin_ws
rosdep install --from-paths src --ignore-src -r -y
catkin_make
source devel/setup.bash
roslaunch prrr_arm_description display.launch
```

## 坐标和关节

全部长度、STL 顶点均为米，角度为弧度；网格 `scale="1 1 1"`。底板安装面为 `base_footprint` 的 Z=0，Z 向上，X 沿伸直的臂方向；SolidWorks 总装坐标到 ROS 的变换是 `(x,y,z)_ROS=(x,-z,y)_SW`。没有加入旧场景的离地 30 毫米假定。

| 关节 | 连接 | 结构 |
|---|---|---|
| `lift_joint` | 底座 → 升降 | 沿 +Z 移动，0～0.300 m，来自原生限位配合 |
| `shoulder_joint` | 升降 → 大臂 | 绕 +Z 旋转 |
| `elbow_joint` | 大臂 → 小臂 | 绕 +Z 旋转，大臂轴距 0.250 m，轴向错层 0.127 m |
| `wrist_joint` | 小臂 → 末端 | 绕 +Z 旋转，小臂轴距 0.200 m，轴向错层 -0.022 m |

三条转动轴在原装配中没有角度限位，所以按 CAD 自由度导出为 `continuous`；这不表示真实管线允许无限旋转。`tool0` 位于工具轴线上、吸盘名义接触面，距末端分总成原点 Z=-0.0185 m。根部增加无质量的 `base_footprint`，把底座惯量放在固定连接的 `base_link` 上。

当前 CAD 姿态如下；`config/cad_pose.json` 和 `.yaml` 用于启动初值，`named_poses.json` 保留其他配置的实际回读值。URDF 中关节位置为零时机械臂伸直，升降处在下限。

| 关节 | 当前值（米或弧度） |
|---|---:|
| `lift_joint` | 0.158935878 |
| `shoulder_joint` | -0.329120660 |
| `elbow_joint` | 0.238261011 |
| `wrist_joint` | 0.090859649 |

## 使用范围和待补参数

已生成用于 ROS 导入、TF 和 RViz 显示的完整模型。含 5 组视觉网格、5 组同几何碰撞网格、质心和惯量，碰撞模型保留真实装配外形，尚未作规划用的简化或全行程碰撞验证。

质量/惯量取自原生 CAD 质量属性，按各组件变换和组合惯量公式合并，并修正 SolidWorks 的惯量积符号；未用外观包围盒代替惯量。当前 CAD 参考总质量约 14.1174 kg。30 种零件未分配原生材料，保留 CAD 默认密度计算值：三毫米二十五长内六角螺钉、三毫米五十五长内六角螺钉、三毫米六角螺母、三毫米十长内六角螺钉、三毫米四十五长内六角螺钉、五毫米一百二十长内六角螺钉、五毫米三十长内六角螺钉、五毫米六角螺母、减速器同步带轮参考、十四号谐波减速器接口参考、升降滑台移动座参考、四毫米六十五长内六角螺钉、四毫米六十长内六角螺钉、四毫米六角螺母、四毫米十六长内六角螺钉、四毫米十四长内六角螺钉、四毫米四十五长内六角螺钉、四毫米气管直通接头参考、导电波纹吸盘参考、带锁紧升降滑台固定部参考、电机同步带轮参考、百瓦伺服电机外形参考、相机与镜头保留空间、立柱安装底板、肘关节同步带参考、肘关节输入延长轴、肩关节输入延长轴、腕部一体化关节输出轴参考、腕部一体化减速伺服固定部参考、谐波减速器转动输出端参考。外购电机、减速器、滑台、相机等仍是接口占位模型，其几何质量不代表厂家实物。

源资料没有可确认的执行器力/速度额定值，因此升降 `<limit>` 中 `effort="0" velocity="0"` 明确表示尚未配置。它们不影响 RViz 的关节位置显示，但会阻止依赖这些限值的控制/规划使用；接入 MoveIt、Gazebo 或实机控制前，需填写真实力、速度、转角限位以及实测/厂家质量惯量，并另外配置控制器。未添加虚构的驱动或控制器参数。

## 验证与复现

交付压缩包中的 `验证结果.json` 为结构、资源、惯量和多个 CAD 配置运动学核对结果，`机械臂URDF预览.png` 为读取实际 URDF 和合并网格生成的预览。源总装的原生检查仍有 47 项几何重叠，保留原装配，不作为碰撞验收通过。当前 Windows 电脑没有 ROS/RViz 运行环境，因此没有声明已在 ROS 运行时启动通过；可在目标电脑安装 `liburdfdom-tools` 后执行 `check_urdf urdf/prrr_arm.urdf`，再运行上面的启动命令。

导出过程与内部零件暂存仅作复现依据，未放入最终 ROS 模型压缩包。交付包只需要此 ROS 包。

接口依据：[SolidWorks 组件变换](https://help.solidworks.com/2025/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IComponent2~Transform2.html)、[质心惯量枚举](https://help.solidworks.com/2024/english/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swMassPropertyMoment_e.html)、[ROS robot_state_publisher](https://github.com/ros/robot_state_publisher)、[joint_state_publisher 初值参数](https://github.com/ros/joint_state_publisher)。
