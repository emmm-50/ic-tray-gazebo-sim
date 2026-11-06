# Gazebo 场景素材与静态预览

本目录保存选中素材的上游原件、许可、预览衍生件和场景图。尺寸来自 SDF 碰撞几何和 STL 顶点包围盒，单位为 mm，Z 以各自的地面或托盘底面为零。预览使用独立世界 `ic_tray_asset_preview`。

[车载分站布局](layout/slam/README.zh-CN.md) · [素材单独预览](preview/scene.sdf) · [素材预览全景](verification/overview.png) · [托盘近景](verification/tray_detail.png)

## 任务书、当前单槽和下载素材

| 对象 | 原任务书目标 | 当前 `task.yaml` 与场景实现 | 下载原件实测 | 本次预览与垫高量 |
| --- | --- | --- | --- | --- |
| 传送带 | 台面高 400，带宽容纳一盘 | 基本体 280 × 180 × 70，取料支撑面 400 | 四腿版 5100 × 1000 × 600，平带长 5000，带面距地 600 | 总长宽高 700 × 180 × 400，平带 650 × 180，支撑面 400。原四腿版比目标高 200，缩短腿并调整带体，落地垫高 0 |
| 货架 | 宽约 860、深 400，两层支撑面 320 / 505，每层五槽，槽距 160，有效跨度 800 | 上、下支撑面 505 / 320，配置单槽、槽距 180、进深 362.6、厚 20。下层为整板，上层为两根支撑梁 | Fuel Bookshelf 外宽 × 进深 × 高为 920 × 405 × 1200，内宽 880。两个中间层支撑面 440 / 810，间距 370，另有底板和顶板 | 860 × 400 × 700，内宽 840。两层实面 320 / 505，间距 185，垫高 0。每层按 160 画五个槽位，标线只参与渲染 |
| IC Tray | 322.6 × 136 × 6.35，7 × 7 芯片，26 × 10 格 | 同尺寸的平盒，配置质量 0.25 kg | QFN 7 × 7 短盘本体长 106.5，含标签 **109.6 × 135.9 × 5.5**，10 × 8 格 | 沿用网格尺寸，长差 −213.0、宽差 −0.1、厚差 −0.85。模型底面 Z=0，预览两件分别落在 Z=400 和 320，无附加垫高 |

任务书把 6.35 mm 用作本组托盘厚度。上表中单槽尺寸取自当前工作区的配置和生成代码。 原任务书《IC Tray盘搬运机器人》保存在本地。 [task.yaml](../../ic_tray_sim/config/task.yaml) · [单槽场景代码](../../ic_tray_sim/ic_tray_sim/scene.py)

原书架两层分别高 120 和 305 mm，同一垫块只会整体平移，层距仍为 370 mm。预览衍生件同步移动两层视觉和碰撞盒，改为目标层距 185 mm。两层均为连续板，五槽为位置标记，未做 L 形托轨、导入口和传感器位置。

官方传送带例的输送体原件无支架，包络为 5100 × 200 × 100，模型原点在带体中心，平带面相对原点 Z=50，底面 Z=−50。用其原尺寸且从地面支承时，需 300 mm 底座和 350 mm 模型原点高度才能使带面到 400 mm。本预览采用经调整的四腿版。

## 素材与 Git 归属

| 素材与用途 | 上游发布和固定版本 | 许可与归属 | 原件和本项目改动 |
| --- | --- | --- | --- |
| 四腿传送带，已预览 | Mohamed Abdelkader Zahana 的 Git 仓库，提交 `4083cef0df5a474634d3603f585d084d77c16494`。[固定源码目录](https://github.com/mzahana/conveyor_sim_ros2/tree/4083cef0df5a474634d3603f585d084d77c16494/models/simple_conveyor) | 仓库 MIT 声明 Copyright (c) 2025 Mohamed Abdelkader Zahana。模型配置作者栏为 Auto Generated。与 Gazebo 示例共享部分 SDF 写法、配色和摩擦参数，原文件未说明关系，额外保留官方 Apache 许可与来源 | [原件及 MIT 许可](upstream/conveyor/conveyor_sim_ros2/) · [预览衍生件](preview/models/ic_tray_conveyor/)。副本移除重复 XML 声明和输送控制插件，调整带体、圆端、四腿的尺寸和位置，保留七组对应的基本体视觉与碰撞。无网格、材质文件依赖 |
| 官方传送带，原件保留作参考 | Gazebo / Open Robotics 项目，`gz-sim8` 提交 `b791db8dd6fecf85f191a8796ff2dd817f951c07`。[固定示例](https://github.com/gazebosim/gz-sim/blob/b791db8dd6fecf85f191a8796ff2dd817f951c07/examples/worlds/conveyor.sdf) | 仓库 Apache-2.0。示例文件无独立作者或版权标头 | [完整原 SDF 与许可](upstream/conveyor/gz-sim8/)。未改。输送体自包含，带体及圆端有对应碰撞；完整示例世界另含演示方块，并定义了 TrackController 和键盘触发 |
| Fuel Bookshelf，已预览 | Fuel 发布者 OpenRobotics，包内作者 Nate Koenig，Fuel 版本 **4**。此发行包的 Git 提交未确认。[模型页](https://app.gazebosim.org/OpenRobotics/fuel/models/Bookshelf) · [固定 ZIP](https://fuel.gazebosim.org/1.0/OpenRobotics/models/Bookshelf/4/Bookshelf.zip) | Fuel API 标注 CC0 1.0。贴图无单列作者声明，沿用包级标注 | [原始模型、贴图和许可](upstream/rack/fuel_bookshelf/) · [预览衍生件](preview/models/ic_tray_rack/)。原 SDF 1.5 有七对 box。副本保留背板、侧板和两个中间层，移除底板、顶板，配对改尺寸与层高，保留原木纹并改为本地模型 URI，移除 Classic 材质脚本引用 |
| QFN 7 × 7 mini-tray，已预览 | CompuPhase 发布，源码版本 **2B**，下载的成品网格没有 Git 提交号。 [作者项目页](https://www.compuphase.com/electronics/minitray.htm) · [原始 STL](https://www.compuphase.com/electronics/minitray-qfn7x7.stl) · [源码 ZIP](https://www.compuphase.com/electronics/minitray_source.zip) | 源文件标注 Copyright 2020–2023 CompuPhase、Apache-2.0。网页页脚另有 CC BY-SA 3.0 和 Thiadmer Riemersma / CompuPhase 署名，随包保留两份许可文本及各自范围说明。独立 STL 无版权头 | [源码、STL 和许可](upstream/tray/compuphase-mini-tray-v2b/) · [预览衍生件](preview/models/ic_tray_mini/)。原 STL 并排放置托盘和盖板。仅提取托盘的 5880 个原三角面，SDF 按毫米转米并居中，保留凹格外观，碰撞用 135.9 × 109.6 × 5.5 的包围盒 |

本机项目的 Git `origin` 为 `emmm-50/ic-tray-gazebo-sim`，表示 GitHub 托管位置。项目未声明统一开源许可。原 PRRR 为 SolidWorks 总装导出，包标注 `Proprietary`，实际权利人和再分发授权未确认。第三方素材的发布者、作者与许可按上表分别记录。 [GitHub 托管仓库](https://github.com/emmm-50/ic-tray-gazebo-sim) · [PRRR 导出说明](../../prrr_arm_description/README.zh-CN.md) · [PRRR 包声明](../../prrr_arm_description/package.xml)

## 核对过的其他候选

- OSRF Git 版 `bookshelf` 也属于木质书架，原始层高和结构与任务目标有差异。该发布渠道仓库标注 CC BY 3.0，本次用带贴图的 Fuel v4。对 Fuel 上 OpenRobotics 的 `Shelf`、`Rack`、`Warehouse Shelf`、`Storage Rack`、`Industrial Shelf`、`Shelving Unit` 精确名称查询均未匹配，未核验到现成的两层五槽导轨架。 [OSRF 固定目录](https://github.com/osrf/gazebo_models/tree/8163eb4b5e7e21985c6591d1c0bfb56468c0093f/bookshelf) · [OSRF 许可](https://github.com/osrf/gazebo_models/blob/8163eb4b5e7e21985c6591d1c0bfb56468c0093f/LICENSE)
- TopLine `QFNTRAY7mm-10x26` 的芯片尺寸和格数与任务书相符，查到产品页及尺寸资料，未找到可下载且许可明确的三维网格，作为尺寸和外观参考。 [TopLine QFN 系列](https://www.topline.tv/tray_qfn.html) · [尺寸资料入口](https://www.topline.tv/drawings/drawview.cfm?draw=1388)
- NIST ARIAC 2023 kit tray 是四分区工装，核对的 SDF 碰撞盒为 380 × 520 × 10，远大于目标托盘且无芯片格。 [固定 Git 版本](https://github.com/usnistgov/ARIAC/tree/215eebf8c8526c98092da30adbb57a2213d210d5) · [工装说明](https://pages.nist.gov/ARIAC_docs/en/2023.5.0/competition/environment.html#kit-trays)
- CompuPhase 同系列 5 × 5 芯片格短盘也已核对，外包络与所选短盘相同，有 14 × 11 格。预览采用同尺寸但芯片规格更贴合的 7 × 7 版。 [5 × 5 原始 STL](https://www.compuphase.com/electronics/minitray-qfn5x5.stl)

## 本机加载与复现

现有 Conda 环境中，Gazebo Sim **8.10.0**（Harmonic）和 libsdformat **14.8.0** 通过最终世界的 SDF 检查及服务端加载。用独立 Gazebo 分区、环回接口和 ROS 域 174，查询到传送带、货架、两个托盘及槽位标线。Ogre2 无界面相机版本只为同一场景增加两台相机，实际渲染两张 1100 × 720 PNG。木纹和托盘网格均出现在渲染中。初试时 DART 日志报告托盘凹网格的 SDF 碰撞构造未实现，最终预览用包围盒代理并复跑。验证覆盖静态加载和渲染，未做抓取、接触或插拔验证。

从项目根目录运行以下命令可复现服务端加载。需要图形预览时可去掉 `-s` 和 `--iterations 20`。本次截图由无界面相机渲染取得。素材 URI 全为本地资源，Gazebo 的 Fuel 缓存路径指向项目目录。

```bash
preview_dir="$PWD/artifacts/asset_sourcing/preview"
preview_cache="$PWD/log/asset_preview/fuel"
mkdir -p "$preview_cache"
bash tools/run_isolated.sh env \
  GZ_PARTITION="ic_tray_asset_preview_$$" ROS_DOMAIN_ID=174 GZ_IP=127.0.0.1 \
  GZ_SIM_RESOURCE_PATH="$preview_dir/models" GZ_FUEL_CACHE_PATH="$preview_cache" \
  gz sim -s -r --iterations 20 -v 3 "$preview_dir/scene.sdf"
```

`run_isolated.sh` 会取消 `HOME`。运行时自动文件日志尝试使用根目录下的 `.gz` 路径并报权限提示，验证日志通过标准输出保存在 `verification/`。选中素材和预览文件已纳入版本管理，运行日志和下载缓存留在本地。
