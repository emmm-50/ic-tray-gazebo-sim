"""Pure helpers for B1 dock errors and optional configured tolerance bounds."""
import math


def tolerance_from_config(config):
    tolerance = config.get('dock_tolerance')
    if tolerance is not None:
        for axis in ('x', 'y', 'yaw'):
            bounds = tolerance[axis]
            if len(bounds) != 2 or not all(math.isfinite(v) for v in bounds) or bounds[0] > bounds[1]:
                raise ValueError(f'invalid dock tolerance for {axis}')
    return tolerance


def dock_error(pose, dock):
    angle = pose[2] - dock[2]
    return pose[0] - dock[0], pose[1] - dock[1], math.atan2(math.sin(angle), math.cos(angle))


def within_tolerance(pose, dock, tolerance):
    if tolerance is None:
        return True
    return all(tolerance[axis][0] <= value <= tolerance[axis][1]
               for axis, value in zip(('x', 'y', 'yaw'), dock_error(pose, dock)))


def dock_center(dock, tolerance):
    angle = dock[2] + sum(tolerance['yaw']) / 2
    return (dock[0] + sum(tolerance['x']) / 2, dock[1] + sum(tolerance['y']) / 2,
            math.atan2(math.sin(angle), math.cos(angle)))
