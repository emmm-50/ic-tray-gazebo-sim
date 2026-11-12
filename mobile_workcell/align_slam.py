"""Register the live SLAM frame to the static Gazebo workcell using lidar."""

import argparse
import math
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import rclpy
from geometry_msgs.msg import TransformStamped
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.time import Time
from scipy.optimize import least_squares
from sensor_msgs.msg import LaserScan
from tf2_ros import Buffer, TransformBroadcaster, TransformException, TransformListener

from layout_geometry import amr_start, boxes, pose


def rotate(xy, yaw):
    c, s = math.cos(yaw), math.sin(yaw)
    return xy @ np.array([[c, s], [-s, c]])


def compose(parent, child):
    return np.r_[parent[:2] + rotate(child[:2], parent[2]), parent[2] + child[2]]


def inverse(pose):
    return np.r_[rotate(-pose[:2], -pose[2]), -pose[2]]


def xy_yaw(transform):
    p, q = transform.translation, transform.rotation
    return np.array([p.x, p.y, math.atan2(2 * (q.w * q.z + q.x * q.y),
                                         1 - 2 * (q.y * q.y + q.z * q.z))])


def reference_segments(sdf, height):
    segments = []
    for name in ('warehouse_perimeter', 'fixed_island', 'west_landmark_cabinet', 'ic_tray_rack_metal'):
        for x, y, z, yaw, (sx, sy, sz), _ in boxes(sdf, {name}):
            if abs(z - height) > sz / 2:
                continue
            corners = np.array([[-sx, -sy], [sx, -sy], [sx, sy], [-sx, sy]]) / 2
            corners = np.array([x, y]) + rotate(corners, yaw)
            segments.extend(zip(corners, np.roll(corners, -1, axis=0)))
    return np.array(segments)


class Alignment(Node):
    def __init__(self, layout, amr):
        super().__init__('workcell_slam_alignment')
        self.start = np.array(amr_start(amr))
        laser = pose(amr.find(".//sensor[@name='laser']"))
        self.laser_offset = np.array([laser[0], laser[1], laser[3]])
        segments = reference_segments(layout, laser[2])
        self.starts = segments[:, 0]
        self.vectors = segments[:, 1] - self.starts
        self.lengths_squared = np.sum(self.vectors ** 2, axis=1)
        self.workcell_from_odom = None
        self.workcell_from_map = None
        self.buffer = Buffer()
        self.listener = TransformListener(self.buffer, self)
        self.broadcaster = TransformBroadcaster(self)
        self.create_subscription(LaserScan, '/scan', self.receive_scan, qos_profile_sensor_data)
        self.create_timer(0.05, self.align)
        self.scan = None
        self.last_report = -1.0

    def receive_scan(self, scan):
        self.scan = scan

    def distances(self, base_pose, points):
        laser_pose = compose(base_pose, self.laser_offset)
        points = laser_pose[:2] + rotate(points, laser_pose[2])
        offsets = points[:, None] - self.starts
        fraction = np.sum(offsets * self.vectors, axis=2) / self.lengths_squared
        delta = offsets - np.clip(fraction, 0, 1)[:, :, None] * self.vectors
        return np.sqrt(np.min(np.sum(delta ** 2, axis=2), axis=1))

    def align(self):
        scan = self.scan
        if scan is None:
            return
        stamp = Time.from_msg(scan.header.stamp)
        try:
            odom = self.buffer.lookup_transform('odom', 'base_link', stamp)
            slam = self.buffer.lookup_transform('map', 'base_link', stamp)
        except TransformException:
            return
        self.scan = None
        odom_base, map_base = xy_yaw(odom.transform), xy_yaw(slam.transform)
        if self.workcell_from_odom is None:
            self.workcell_from_odom = compose(self.start, inverse(odom_base))
        seed = compose(self.workcell_from_odom, odom_base)

        ranges = np.array(scan.ranges)
        angles = scan.angle_min + np.arange(len(ranges)) * scan.angle_increment
        # Discard short returns from the carried equipment and the adjacent conveyor.
        valid = (ranges > 0.45) & (ranges < scan.range_max)
        points = ranges[valid, None] * np.column_stack((np.cos(angles[valid]), np.sin(angles[valid])))
        points = points[::2]
        points = points[self.distances(seed, points) < 0.16]
        if len(points) < 24:
            return
        fit = least_squares(self.distances, seed, args=(points,), diff_step=1e-5,
                            loss='soft_l1', f_scale=0.008, max_nfev=18)
        residual = float(np.median(self.distances(fit.x, points)))
        if residual > 0.022 or np.linalg.svd(fit.jac, compute_uv=False)[-1] < 1.0:
            return
        self.workcell_from_odom = compose(fit.x, inverse(odom_base))
        # Keep the current registration while SLAM agrees with the lidar fit.
        # Re-anchor on observable drift, including discontinuous SLAM corrections.
        if self.workcell_from_map is not None:
            predicted = compose(self.workcell_from_map, map_base)
            heading_error = predicted[2] - fit.x[2]
            angle_error = abs(math.atan2(math.sin(heading_error), math.cos(heading_error)))
            drifted = np.linalg.norm(predicted[:2] - fit.x[:2]) > 0.003 or angle_error > 0.004
        else:
            drifted = True
        if drifted:
            self.workcell_from_map = compose(fit.x, inverse(map_base))
        workcell_base = compose(self.workcell_from_map, map_base)

        transform = TransformStamped()
        transform.header.stamp = scan.header.stamp
        transform.header.frame_id = 'workcell'
        transform.child_frame_id = 'map'
        t, q = transform.transform.translation, transform.transform.rotation
        t.x, t.y = self.workcell_from_map[:2]
        half_yaw = self.workcell_from_map[2] / 2
        q.z, q.w = math.sin(half_yaw), math.cos(half_yaw)
        self.broadcaster.sendTransform(transform)
        seconds = stamp.nanoseconds / 1e9
        if seconds - self.last_report >= 1.0:
            self.last_report = seconds
            self.get_logger().info(
                f't={seconds:.2f} workcell_base={workcell_base.tolist()} '
                f'map_base={map_base.tolist()} match={len(points)} median={residual:.4f} m'
            )


def main():
    project = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--layout', type=Path,
                        default=project / 'artifacts/asset_sourcing/layout/slam/slam_workcell.sdf')
    parser.add_argument('--amr', type=Path, default=project / 'mobile_workcell/amr.sdf')
    args = parser.parse_args()
    rclpy.init()
    node = Alignment(ET.parse(args.layout), ET.parse(args.amr))
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
