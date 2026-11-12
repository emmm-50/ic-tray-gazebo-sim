"""Express a nominal B1 placement in a measured, stopped chassis frame.

The pose JSON is the chassis (x, y, yaw) in the same world frame as B1.
"""
import argparse
import json
import math
from pathlib import Path
import sys

import yaml

from dock_tolerance import dock_error, tolerance_from_config, within_tolerance

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'ic_tray_sim'))
from ic_tray_sim.kinematics import b1_approach_xy, b1_waypoints
from ic_tray_sim.scene import arm_mount_pose, b1_dock_pose


def corrected_config(cfg, pose):
    placement = cfg['placement']
    nominal_x, nominal_y, nominal_yaw = arm_mount_pose(b1_dock_pose(cfg))
    measured_x, measured_y, yaw = arm_mount_pose((pose['x'], pose['y'], pose['yaw']))
    c, s = math.cos(yaw), math.sin(yaw)
    nc, ns = math.cos(nominal_yaw), math.sin(nominal_yaw)

    def transform(x, y):
        # Nominal arm-frame point -> world -> measured arm frame.
        world_x = nominal_x + nc * x - ns * y
        world_y = nominal_y + ns * x + nc * y
        dx, dy = world_x - measured_x, world_y - measured_y
        return [c * dx + s * dy, -s * dx + c * dy]

    x, y, z = placement['tool']
    approach_x, approach_y = b1_approach_xy(placement)
    placement['tool'] = [*transform(x, y), z]
    placement['approach_xy'] = transform(approach_x, approach_y)
    yaw_delta = nominal_yaw + placement.get('yaw', 0.0) - yaw
    placement['yaw'] = math.atan2(math.sin(yaw_delta), math.cos(yaw_delta))

    # Check each commanded Cartesian waypoint before any arm motion.
    b1_waypoints(cfg, placement)
    return cfg


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pose', type=Path, help='Stopped chassis pose JSON: x, y, yaw in world')
    parser.add_argument('output', type=Path, help='Corrected task YAML')
    parser.add_argument('--config', type=Path, default=ROOT / 'ic_tray_sim/config/b1_place.yaml')
    args = parser.parse_args()
    cfg = yaml.safe_load(args.config.read_text())
    if cfg.get('mode') != 'b1_place':
        raise ValueError('Expected a B1 placement config')
    pose = json.loads(args.pose.read_text())
    tolerance = tolerance_from_config(cfg)
    if tolerance is not None:
        measured = (pose['x'], pose['y'], pose['yaw'])
        dock = b1_dock_pose(cfg)
        if not within_tolerance(measured, dock, tolerance):
            dx, dy, dyaw = dock_error(measured, dock)
            parser.error(f'B1 needs re-docking before placement: dx={dx:.4f} m, '
                         f'dy={dy:.4f} m, dyaw={dyaw:.4f} rad')
    corrected_config(cfg, pose)
    args.output.write_text(yaml.safe_dump(cfg, sort_keys=False))
    print(f'Corrected B1 config: {args.output}')


if __name__ == '__main__':
    main()
