"""Generate the movable workcell from the shared SLAM layout."""
from copy import deepcopy
from pathlib import Path
import argparse
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
ARM_MOUNT = tuple(json.loads((ROOT / 'ic_tray_sim/ic_tray_sim/mount.json').read_text()))


def write_world(output_path):
    world_tree = ET.parse(ROOT / "artifacts/asset_sourcing/layout/slam/slam_workcell.sdf")
    world = world_tree.getroot().find("world")
    world.set("name", "ic_tray_mobile_workcell")
    robot = ET.parse(Path(__file__).with_name("amr.sdf")).getroot().find("model")
    arm = world.find("model[@name='prrr_mounted_static_visual']/link")
    base = robot.find("link[@name='base_link']")
    # Place arm visuals using the shared chassis-to-arm mounting offset.
    for visual in arm.findall("visual"):
        visual = deepcopy(visual)
        pose = visual.find("pose")
        values = [float(value) for value in pose.text.split()]
        for i, offset in enumerate(ARM_MOUNT):
            values[i] += offset
        pose.text = " ".join(str(value) for value in values)
        visual.set("name", "arm_" + visual.get("name"))
        base.append(visual)
    original = world.find("model[@name='amr_static_envelope']")
    position = list(world).index(original)
    world.remove(original)
    world.remove(world.find("model[@name='prrr_mounted_static_visual']"))
    world.insert(position, robot)
    sensor_system = ET.Element("plugin", {"filename": "gz-sim-sensors-system", "name": "gz::sim::systems::Sensors"})
    ET.SubElement(sensor_system, "render_engine").text = "ogre2"
    world.insert(3, sensor_system)
    ET.indent(world_tree, space="  ")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    world_tree.write(output_path, encoding="utf-8", xml_declaration=True)
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", help="Output SDF path")
    print(write_world(parser.parse_args().output))
