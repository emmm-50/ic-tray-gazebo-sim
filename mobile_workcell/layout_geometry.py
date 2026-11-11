"""Planar poses and box collisions from the workcell's SDF layout."""
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_AMR = ROOT / 'mobile_workcell/amr.sdf'
DEFAULT_B1_CONFIG = ROOT / 'ic_tray_sim/config/b1_place.yaml'


def pose(element):
    values = [float(v) for v in element.findtext('pose', '0 0 0 0 0 0').split()]
    return values[0], values[1], values[2], values[5]


def compose(parent, child):
    x, y, z, yaw = parent
    cx, cy, cz, cyaw = child
    c, s = math.cos(yaw), math.sin(yaw)
    return x + c * cx - s * cy, y + s * cx + c * cy, z + cz, yaw + cyaw


def parse_sdf(source):
    return source if isinstance(source, ET.ElementTree) else ET.parse(source)


def boxes(source, models):
    """Yield x, y, z, yaw, size, name in layout order for selected models."""
    tree = parse_sdf(source)
    for model in tree.findall('./world/model'):
        name = model.get('name')
        if name not in models:
            continue
        model_pose = pose(model)
        for link in model.findall('link'):
            link_pose = compose(model_pose, pose(link))
            for collision in link.findall('collision'):
                size = collision.findtext('geometry/box/size')
                if size:
                    x, y, z, yaw = compose(link_pose, pose(collision))
                    yield x, y, z, yaw, tuple(map(float, size.split())), name


def amr_start(source=DEFAULT_AMR):
    x, y, _, yaw = pose(parse_sdf(source).find('model'))
    return x, y, yaw


def b1_dock(config=DEFAULT_B1_CONFIG):
    import yaml
    sys.path.insert(0, str(ROOT / 'ic_tray_sim'))
    from ic_tray_sim.scene import b1_dock_pose
    with open(config, encoding='utf-8') as f:
        return b1_dock_pose(yaml.safe_load(f))
