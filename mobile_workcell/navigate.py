#!/usr/bin/env python3
"""A-to-B1 reference-route navigator. All control poses are in workcell TF."""
import argparse
import csv
import json
import heapq
import math
import time
from pathlib import Path

from layout_geometry import DEFAULT_AMR, DEFAULT_B1_CONFIG, amr_start, b1_dock, boxes as layout_boxes

def wrap(a):
    return math.atan2(math.sin(a), math.cos(a))

def compose(a, b):
    c, s = (math.cos(a[2]), math.sin(a[2]))
    return (a[0] + c * b[0] - s * b[1], a[1] + s * b[0] + c * b[1], wrap(a[2] + b[2]))

def boxes(sdf):
    allowed = {'warehouse_perimeter', 'fixed_island', 'west_landmark_cabinet', 'rack_riser', 'ic_tray_rack_metal', 'conveyor_risers'}
    result = [(x, y, wrap(yaw), sx / 2, sy / 2, name)
              for x, y, _, yaw, (sx, sy, _), name in layout_boxes(sdf, allowed)]
    result.append((-2.91, -1.2, math.pi / 2, 0.35, 0.09, 'conveyor'))
    if not result:
        raise ValueError('no reference obstacles found in SDF')
    return result

def overlaps(a, b):
    ax, ay, aa, ahx, ahy = a
    bx, by, ba, bhx, bhy = b[:5]
    au = (math.cos(aa), math.sin(aa))
    av = (-au[1], au[0])
    bu = (math.cos(ba), math.sin(ba))
    bv = (-bu[1], bu[0])
    dx, dy = (bx - ax, by - ay)
    for ux, uy in (au, av, bu, bv):
        d = abs(dx * ux + dy * uy)
        ra = ahx * abs(au[0] * ux + au[1] * uy) + ahy * abs(av[0] * ux + av[1] * uy)
        rb = bhx * abs(bu[0] * ux + bu[1] * uy) + bhy * abs(bv[0] * ux + bv[1] * uy)
        if d >= ra + rb:
            return False
    return True

def check_route(obstacles, start=None):
    start = amr_start() if start is None else start
    segments = [(start, (-1.45, -1.2, math.pi))]
    for a, b in segments:
        distance = math.hypot(b[0] - a[0], b[1] - a[1])
        da = wrap(b[2] - a[2])
        steps = max(1, math.ceil(distance / 0.01), math.ceil(abs(da) / 0.02))
        for i in range(steps + 1):
            t = i / steps
            p = (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]), a[2] + t * da, 0.37, 0.245)
            for obstacle in obstacles:
                if overlaps(p, obstacle):
                    raise RuntimeError(f'reference route collision at {p[:3]} with {obstacle[5]}')
    print(f'A escape: checked {len(obstacles)} obstacle boxes', flush=True)

def plan_route(obstacles, dock=None):
    """A* over configuration-space obstacles; simplify with checked sight lines."""
    dock = b1_dock() if dock is None else dock
    resolution = 0.05
    xmin = -3.55
    ymin = -2.25
    nx = 143
    ny = 102
    radius = math.hypot(0.37, 0.245) + 0.03

    def free(x, y):
        if not (-3.55 + radius <= x <= 3.55 - radius and -2.25 + radius <= y <= 2.8 - radius):
            return False
        for ox, oy, a, hx, hy, _ in obstacles:
            c, s = (math.cos(a), math.sin(a))
            dx = x - ox
            dy = y - oy
            u = abs(c * dx + s * dy) - hx
            v = abs(-s * dx + c * dy) - hy
            if math.hypot(max(u, 0), max(v, 0)) <= radius:
                return False
        return True

    def point(cell):
        return (xmin + cell[0] * resolution, ymin + cell[1] * resolution)

    def cell(p):
        return (round((p[0] - xmin) / resolution), round((p[1] - ymin) / resolution))
    start = cell((-1.45, -1.2))
    goal = cell(dock[:2])
    cache = {}

    def valid(n):
        if n not in cache:
            cache[n] = 0 <= n[0] < nx and 0 <= n[1] < ny and free(*point(n))
        return cache[n]
    if not valid(start) or not valid(goal):
        raise RuntimeError('route anchor is occupied')
    costs = {start: 0}
    previous = {}
    queue = [(0, start)]
    while queue:
        _, cur = heapq.heappop(queue)
        if cur == goal:
            break
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            nxt = (cur[0] + dx, cur[1] + dy)
            if not valid(nxt) or (dx and dy and (not valid((cur[0] + dx, cur[1])) or not valid((cur[0], cur[1] + dy)))):
                continue
            g = costs[cur] + math.hypot(dx, dy)
            if g < costs.get(nxt, float('inf')):
                costs[nxt] = g
                previous[nxt] = cur
                heapq.heappush(queue, (g + math.dist(nxt, goal), nxt))
    if goal not in costs:
        raise RuntimeError('no route through reference occupancy grid')
    path = [goal]
    while path[-1] != start:
        path.append(previous[path[-1]])
    path.reverse()
    pts = [point(n) for n in path]
    pts[0] = (-1.45, -1.2)
    pts[-1] = tuple(dock[:2])

    def clear(a, b):
        n = max(1, math.ceil(math.dist(a, b) / 0.01))
        return all((free(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n + 1)))
    route = [pts[0]]
    i = 0
    while i < len(pts) - 1:
        j = len(pts) - 1
        while j > i + 1 and (not clear(pts[i], pts[j])):
            j -= 1
        if not clear(pts[i], pts[j]):
            raise RuntimeError('grid path did not pass continuous clearance check')
        route.append(pts[j])
        i = j
    print('A* reference route:', route, flush=True)
    return route

def yaw_from_quaternion(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))

def map_obstacles(grid, transform):
    """Transform occupied map cells into the calibrated workcell frame."""
    origin = grid.info.origin
    tf = transform.transform
    workcell_from_map = (tf.translation.x, tf.translation.y, yaw_from_quaternion(tf.rotation))
    map_from_grid = (origin.position.x, origin.position.y, yaw_from_quaternion(origin.orientation))
    workcell_from_grid = compose(workcell_from_map, map_from_grid)
    resolution = grid.info.resolution
    result = []
    for i, value in enumerate(grid.data):
        if value < 65:
            continue
        x = (i % grid.info.width + 0.5) * resolution
        y = (i // grid.info.width + 0.5) * resolution
        px, py, heading = compose(workcell_from_grid, (x, y, 0))
        result.append((px, py, heading, resolution / 2, resolution / 2, 'slam_map'))
    return result

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sdf', required=True)
    ap.add_argument('--output', required=True)
    ap.add_argument('--csv', required=True)
    ap.add_argument('--offline-check', action='store_true')
    ap.add_argument('--amr', type=Path, default=DEFAULT_AMR)
    ap.add_argument('--config', type=Path, default=DEFAULT_B1_CONFIG)
    args = ap.parse_args()
    obstacles = boxes(args.sdf)
    start = amr_start(args.amr)
    dock = b1_dock(args.config)
    check_route(obstacles, start)
    if args.offline_check:
        plan_route(obstacles, dock)
        return
    import rclpy
    from rclpy.node import Node
    from rclpy.time import Time
    from geometry_msgs.msg import Twist
    from nav_msgs.msg import Odometry, OccupancyGrid
    from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
    from tf2_ros import Buffer, TransformException, TransformListener

    class Navigator(Node):

        def __init__(self):
            super().__init__('reference_route_navigator', parameter_overrides=[rclpy.parameter.Parameter('use_sim_time', value=True)])
            self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
            self.create_subscription(Odometry, '/odom', self.odom_cb, 10)
            self.buf = Buffer()
            self.listener = TransformListener(self.buf, self)
            qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL, reliability=ReliabilityPolicy.RELIABLE)
            self.map = None
            self.create_subscription(OccupancyGrid, '/map', self.map_cb, qos)
            self.route = None
            self.waypoint = 1
            self.stage = 0
            self.odom = None
            self.odom_wall = 0
            self.still_since = None
            self.started = time.monotonic()
            self.last_log = 0
            self.done = False
            self.csvfile = open(args.csv, 'w', newline='')
            self.writer = csv.writer(self.csvfile)
            self.writer.writerow(['stage', 'time', 'x', 'y', 'yaw'])
            self.names = ['backout', 'align', 'follow', 'final_yaw', 'settle']
            self.timer = self.create_timer(0.05, self.tick)

        def map_cb(self, msg):
            self.map = msg

        def odom_cb(self, msg):
            self.odom = (msg.twist.twist.linear.x, msg.twist.twist.angular.z)
            self.odom_wall = time.monotonic()

        def command(self, v=0.0, w=0.0):
            m = Twist()
            m.linear.x = float(v)
            m.angular.z = float(w)
            self.pub.publish(m)

        def advance(self):
            self.command()
            self.stage += 1
            self.still_since = None
            print('stage:', self.names[self.stage] if self.stage < len(self.names) else 'done', flush=True)

        def wait_for_pose(self):
            self.still_since = None
            self.command()

        def tick(self):
            if time.monotonic() - self.started > 360:
                self.command()
                raise RuntimeError('navigation timed out')
            try:
                t = self.buf.lookup_transform('workcell', 'base_link', Time())
            except TransformException:
                self.wait_for_pose()
                return
            if self.route is None:
                if self.map is None:
                    self.command()
                    return
                try:
                    map_tf = self.buf.lookup_transform('workcell', self.map.header.frame_id, Time())
                except TransformException:
                    self.command()
                    return
                overlay = map_obstacles(self.map, map_tf)
                merged = obstacles + overlay
                print(f'SLAM map overlay: {len(overlay)} occupied cells, {self.map.info.width} x {self.map.info.height}, resolution {self.map.info.resolution:.3f} m', flush=True)
                check_route(merged, start)
                self.route = plan_route(merged, dock)
            x = t.transform.translation.x
            y = t.transform.translation.y
            yaw = yaw_from_quaternion(t.transform.rotation)
            now = self.get_clock().now().nanoseconds / 1e9
            stamp = Time.from_msg(t.header.stamp).nanoseconds / 1e9
            if now - stamp > 0.5:
                self.wait_for_pose()
                return
            if now - self.last_log >= 0.1:
                self.writer.writerow([self.names[self.stage], f'{now:.3f}', x, y, yaw])
                self.csvfile.flush()
                self.last_log = now
            if self.odom is None or time.monotonic() - self.odom_wall > 1.0:
                self.wait_for_pose()
                return
            if self.stage == 0:
                self.line(x, y, yaw, -1.45, -1.2, True, 0.02)
            elif self.stage == 1:
                tx, ty = self.route[self.waypoint]
                self.turn(yaw, math.atan2(ty - y, tx - x))
            elif self.stage == 2:
                tx, ty = self.route[self.waypoint]
                if math.hypot(tx - x, ty - y) < (0.012 if self.waypoint == len(self.route) - 1 else 0.025):
                    self.command()
                    if self.waypoint == len(self.route) - 1:
                        self.stage = 3
                    else:
                        self.waypoint += 1
                        self.stage = 1
                    print('waypoint:', self.waypoint, 'stage:', self.names[self.stage], flush=True)
                else:
                    self.line(x, y, yaw, tx, ty, False, 0.001)
            elif self.stage == 3:
                self.turn(yaw, dock[2])
            else:
                self.command()
                if abs(self.odom[0]) < 0.005 and abs(self.odom[1]) < 0.01:
                    if self.still_since is None:
                        self.still_since = time.monotonic()
                    if time.monotonic() - self.still_since > 1.0:
                        Path(args.output).write_text(json.dumps({'x': x, 'y': y, 'yaw': yaw}, indent=2) + '\n')
                        print('stopped:', x, y, yaw, flush=True)
                        self.done = True
                else:
                    self.still_since = None

        def turn(self, yaw, target):
            e = wrap(target - yaw)
            if abs(e) < 0.012:
                self.advance()
                return
            self.command(0, max(-0.45, min(0.45, 1.3 * e)))

        def line(self, x, y, yaw, tx, ty, reverse, tol):
            dx, dy = (tx - x, ty - y)
            dist = math.hypot(dx, dy)
            if dist < tol:
                self.advance()
                return
            target = math.atan2(dy, dx) + (math.pi if reverse else 0.0)
            error = wrap(target - yaw)
            if abs(error) > 1.1:
                self.command(0, max(-0.35, min(0.35, error)))
                return
            v = min(0.16, max(0.025, 0.65 * dist)) * max(0.0, math.cos(error))
            self.command(-v if reverse else v, max(-0.4, min(0.4, 1.5 * error)))
    rclpy.init()
    node = Navigator()
    try:
        while rclpy.ok() and (not node.done):
            rclpy.spin_once(node, timeout_sec=0.1)
    finally:
        node.command()
        node.csvfile.close()
        node.destroy_node()
        rclpy.shutdown()
if __name__ == '__main__':
    main()
