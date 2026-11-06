# 货架素材来源与预览

- 上游：[OpenRobotics / Bookshelf](https://app.gazebosim.org/OpenRobotics/fuel/models/Bookshelf)，Fuel 版本 4，[固定版本下载](https://fuel.gazebosim.org/1.0/OpenRobotics/models/Bookshelf/4/Bookshelf.zip)。上游包内 `model.config` 作者为 Nate Koenig；本次 Fuel API 元数据标注 CC0 1.0，见 `fuel_bookshelf/fuel-metadata.json` 与 [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)。Fuel 版本号 4 不同于包内 model.config 的 1.0。
- 解压后的模型和纹理保留在 `fuel_bookshelf/`。完整 ZIP 含缩略图，可从上述固定链接取得。上游为 SDF 1.5，7 对 box 视觉与碰撞；原始外边界 0.92 × 0.405 × 1.2 m，内宽 0.88 m；两个中间层板上表面为 0.44 和 0.81 m，间隔 0.37 m。还包括底板和顶板。木纹依赖包内 `bookshelf_diffuse.jpg`，另有 Gazebo Classic 材质脚本引用。
- 预览衍生件 `../../preview/models/ic_tray_rack/`：尺寸改为 0.86 × 0.4 × 0.7 m、内宽 0.84 m；两层板上表面 0.320、0.505 m，间隔 0.185 m。保留背板和侧板，移除原底板和顶板；所有视觉与碰撞 box 成对同步修改。无槽位线或分隔结构。每层 5 个中心可为 x = -0.32、-0.16、0、0.16、0.32 m；槽位间距 0.16 m。
- 保留原始纹理并将其 URI 改为 `model://ic_tray_rack/bookshelf_diffuse.jpg`，删除 Classic 材质脚本引用。需将 `preview/models` 加入 `GZ_SIM_RESOURCE_PATH`；使用 `model://ic_tray_rack` 引入。本项目衍生件已加载并渲染。 [验证记录](../../README.zh-CN.md#本机加载与复现)
- 项目 README 提到的旧 [osrf/gazebo_models bookshelf](https://github.com/osrf/gazebo_models/tree/8163eb4b5e7e21985c6591d1c0bfb56468c0093f/bookshelf) 属于另一发布渠道，仓库许可为 CC BY 3.0；本次选择 Fuel 版，不以仓库许可替代 Fuel 元数据。
