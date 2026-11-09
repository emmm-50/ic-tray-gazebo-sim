"""Execute one transfer and require action results and plugin state transitions."""
import sys
import time
from pathlib import Path
import yaml
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy
from ament_index_python.packages import get_package_share_directory
from control_msgs.action import FollowJointTrajectory
from control_msgs.msg import JointTolerance
from trajectory_msgs.msg import JointTrajectoryPoint
from std_msgs.msg import Empty, String
from .kinematics import JOINTS, TOOL_Z0, solve


class Transfer(Node):
    def __init__(self):
        super().__init__('ic_tray_pick_place')
        default = str(Path(get_package_share_directory('ic_tray_sim')) / 'config/task.yaml')
        self.declare_parameter('task_config', default)
        with open(self.get_parameter('task_config').value, encoding='utf-8') as f:
            self.cfg = yaml.safe_load(f)
        self.client = ActionClient(self, FollowJointTrajectory, '/arm_controller/follow_joint_trajectory')
        self.attach = self.create_publisher(Empty, '/suction/attach', 10)
        self.detach = self.create_publisher(Empty, '/suction/detach', 10)
        self.state = None
        self.create_subscription(String, '/suction/state', self.on_state,
                                 QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL))

    def on_state(self, msg):
        self.state = msg.data.lower()
        self.get_logger().info('Suction state: ' + msg.data)

    def wait_future(self, future, timeout):
        end = time.monotonic() + timeout
        while rclpy.ok() and not future.done() and time.monotonic() < end:
            rclpy.spin_once(self, timeout_sec=0.1)
        if not future.done():
            raise RuntimeError('Controller timed out')
        return future.result()

    def suction(self, attached):
        desired = 'attached' if attached else 'detached'
        pub = self.attach if attached else self.detach
        deadline = time.monotonic() + 8
        while rclpy.ok() and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=.1)
            if self.state == desired:
                return
            pub.publish(Empty())
        raise RuntimeError('No Gazebo suction state confirmation: ' + desired)

    def move(self, label, *positions):
        self.get_logger().info(label + ': ' + ', '.join(f'{v:.3f}' for v in positions[-1]))
        goal = FollowJointTrajectory.Goal()
        goal.trajectory.joint_names = JOINTS
        goal.goal_tolerance = [JointTolerance(name=name, position=.002 if name == 'lift_joint' else .01) for name in JOINTS]
        goal.goal_time_tolerance.sec = 3
        for i, position in enumerate(positions):
            point = JointTrajectoryPoint(); point.positions = position
            elapsed_ns = (i + 1) * 5_000_000_000 // len(positions)
            point.time_from_start.sec, point.time_from_start.nanosec = divmod(elapsed_ns, 1_000_000_000)
            goal.trajectory.points.append(point)
        handle = self.wait_future(self.client.send_goal_async(goal), 10)
        if not handle or not handle.accepted:
            raise RuntimeError('Trajectory rejected: ' + label)
        result = self.wait_future(handle.get_result_async(), 20)
        if result.status != 4 or result.result.error_code != 0:
            raise RuntimeError(f'Trajectory failed: {label}, status={result.status}, error={result.result.error_code}')

    def place_b1(self, target):
        """Place an attached tray using tool coordinates in the arm frame."""
        deadline = time.monotonic() + 8
        while self.state is None and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=.1)
        if self.state != 'attached':
            raise RuntimeError('B1 requires an already attached tray')
        x, y, z = target['tool']
        approach_x = target['approach_x']
        travel = TOOL_Z0 + self.cfg['travel_lift']
        approach = solve(approach_x, y, travel)
        self.move('B1 approach', approach)
        insert = [solve(approach_x + (x - approach_x) * i / 8, y, travel) for i in range(1, 9)]
        self.move('B1 insert', *insert)
        self.move('B1 lower', solve(x, y, z))
        self.suction(False)
        self.move('B1 lift tool', insert[-1])
        self.move('B1 retreat', approach)
        self.get_logger().info('B1 placement complete')

    def run(self):
        if not self.client.wait_for_server(timeout_sec=30):
            raise RuntimeError('Trajectory controller unavailable')
        c = self.cfg
        if c.get('mode') == 'b1_place':
            self.place_b1(c['placement'])
            return
        p = c['pickup']; t = c['tray']
        gap = c['suction_gap']; travel = TOOL_Z0 + c['travel_lift']
        pick_z = p['surface'] + t['size'][2] + gap
        pickup = solve(p['x'], p['y'], pick_z)
        pickup_approach = solve(p['x'], p['y'], travel)
        if c.get('mode') == 'a_pickup':
            stow = solve(*c['stow'], travel)
        else:
            s = c['shelf']
            place_z = s['levels'][-1] + t['size'][2] + gap
            shelf_approach = solve(s['x'], s['y'], travel)
            placement = solve(s['x'], s['y'], place_z)
        self.get_logger().info('Release startup joint, then descend to pickup')
        self.suction(False)
        self.move('pickup', pickup)
        self.suction(True)
        self.move('lift tray', pickup_approach)
        if c.get('mode') == 'a_pickup':
            self.move('stow with tray', stow)
            self.get_logger().info('A pickup complete: tray remains attached')
            return
        self.move('above upper middle shelf', shelf_approach)
        self.move('place tray', placement)
        self.suction(False)
        self.move('retreat', shelf_approach)
        self.get_logger().info('Transfer complete: trajectory actions and suction transitions confirmed')


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = Transfer(); node.run()
    except Exception as exc:
        print('Transfer failed:', exc, file=sys.stderr)
        return 1
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()
    return 0
