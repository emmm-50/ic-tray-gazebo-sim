"""Planar PRRR inverse kinematics; all distances in metres."""
import math

BASE_X, L1, L2, TOOL_Z0 = 0.12, 0.25, 0.20, 0.2855
JOINTS = ['lift_joint', 'shoulder_joint', 'elbow_joint', 'wrist_joint']

def solve(x, y, z, yaw=0.0):
    x -= BASE_X
    c = (x*x + y*y - L1**2 - L2**2) / (2 * L1 * L2)
    if not -1.0 <= c <= 1.0:
        raise ValueError('Target outside planar reach')
    lift = z - TOOL_Z0
    if not 0.0 <= lift <= 0.3:
        raise ValueError('Target outside lift range')
    elbow = math.acos(c)
    shoulder = math.atan2(y, x) - math.atan2(L2 * math.sin(elbow), L1 + L2 * math.cos(elbow))
    return [lift, shoulder, elbow, yaw - shoulder - elbow]

def forward(q):
    lift, shoulder, elbow, wrist = q
    return (BASE_X + L1*math.cos(shoulder) + L2*math.cos(shoulder+elbow),
            L1*math.sin(shoulder) + L2*math.sin(shoulder+elbow),
            TOOL_Z0 + lift, shoulder + elbow + wrist)
