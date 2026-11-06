# IC mini tray preview

The tray mesh is extracted from CompuPhase's original `minitray-qfn7x7.stl` by retaining all 5,880 triangles with Y < 110 mm. No triangle crosses that cut. The separate lid is omitted. The original mesh, source and license texts are in [the upstream directory](../../../upstream/tray/compuphase-mini-tray-v2b/). The source identifies version 2B, Copyright 2020–2023 CompuPhase, Apache-2.0. The web page footer separately states CC BY-SA 3.0. [Author's project page](https://www.compuphase.com/electronics/minitray.htm)

The source units are millimetres. Extracted bounds are X 0–135.9, Y 0–109.6, Z 0–5.5 mm. The 3.1 mm tab is included in Y. SDF scale converts the mesh to metres and the visual pose centers it in X and Y. The model origin lies on the underside and the 10 × 8 pockets face +Z. Collision is a box using the mesh envelope. The preview uses the short tray in its native proportions. [Static Gazebo verification](../../../README.zh-CN.md#本机加载与复现)
