# Static tray conveyor

Adapted from `models/simple_conveyor` in [mzahana/conveyor_sim_ros2](https://github.com/mzahana/conveyor_sim_ros2), commit `4083cef0df5a474634d3603f585d084d77c16494`. Copyright (c) 2025 Mohamed Abdelkader Zahana; MIT license in `LICENSE`. The upstream original and its license are preserved in `artifacts/asset_sourcing/upstream/conveyor/conveyor_sim_ros2/`.

Changes: duplicate XML declaration corrected, control plugins removed, belt, rollers and legs resized and repositioned; original colors and corresponding collision shapes retained. Ground center is model origin; length is X, width is Y. Overall extents are X ±0.35 m, Y ±0.09 m, Z 0–0.40 m. Flat belt is 0.65 × 0.18 m, top at Z=0.40 m; rounded ends extend to overall 0.70 m. Static model, no external meshes or materials.

The official gz-sim8 example is preserved separately at `artifacts/asset_sourcing/upstream/conveyor/gz-sim8/`. [Static Gazebo verification](../../../README.zh-CN.md#本机加载与复现).
