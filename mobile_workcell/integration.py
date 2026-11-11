"""Build the opt-in mobile manipulator world from the existing models."""
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

import yaml
from ic_tray_sim.scene import robot_xml, tray_sdf, tray_position
from world import ARM_MOUNT, ROOT, write_world


def build(run_dir):
    run_dir = Path(run_dir)
    cfg = yaml.safe_load((ROOT / 'ic_tray_sim/config/a_pickup.yaml').read_text())
    xml = ET.fromstring(robot_xml(ROOT / 'prrr_arm_description', ROOT / 'ic_tray_sim/config/controllers.yaml', cfg))
    # The arm URDF has its own base_link, distinct from the mobile chassis.
    for elem in xml.iter():
        for key, value in list(elem.attrib.items()):
            if value == 'base_link':
                elem.set(key, 'arm_base_link')
    xml.remove(xml.find("link[@name='world']"))
    chassis = ET.SubElement(xml, 'link', {'name': 'base_link'})
    # gz sdf -p needs valid inertia to retain the mount; this temporary link is discarded.
    inertial = ET.SubElement(chassis, 'inertial')
    ET.SubElement(inertial, 'mass', {'value': '20'})
    ET.SubElement(inertial, 'inertia', {'ixx': '1', 'iyy': '1', 'izz': '1', 'ixy': '0', 'ixz': '0', 'iyz': '0'})
    joint = xml.find("joint[@name='world_fixed']")
    joint.find('parent').set('link', 'base_link')
    joint.find('origin').set('xyz', ' '.join(map(str, ARM_MOUNT)))
    joint.find('origin').set('rpy', '0 0 0')
    # Preserve the chassis/arm fixed joint during conversion to flat SDF.
    gazebo = ET.SubElement(xml, 'gazebo', {'reference': 'world_fixed'})
    ET.SubElement(gazebo, 'preserveFixedJoint').text = 'true'
    urdf = run_dir / 'robot.urdf'
    urdf.write_text(ET.tostring(xml, encoding='unicode'))
    sdf = subprocess.run(['gz', 'sdf', '-p', str(urdf)], check=True, capture_output=True, text=True).stdout
    arm = ET.fromstring(sdf).find('model')
    # Discard the temporary converter chassis and retain the original mobile chassis.
    arm.remove(arm.find("link[@name='base_link']"))
    world_file = write_world(run_dir / 'mobile_workcell.sdf')
    tree = ET.parse(world_file)
    world = tree.getroot().find('world')
    world.find('physics/max_step_size').text = '0.001'
    ET.SubElement(world, 'plugin', {'filename': 'gz-sim-user-commands-system', 'name': 'gz::sim::systems::UserCommands'})
    for include in list(world.findall('include')):
        if include.findtext('name', '').startswith('mini_tray_'):
            world.remove(include)
    robot = world.find("model[@name='ic_tray_mobile']")
    for visual in list(robot.find("link[@name='base_link']").findall('visual')):
        if visual.get('name', '').startswith('arm_'):
            robot.find("link[@name='base_link']").remove(visual)
    for child in list(arm):
        robot.append(child)
    ET.indent(tree, space='  ')
    tree.write(world_file, encoding='utf-8', xml_declaration=True)
    return world_file, urdf.read_text(), tray_sdf(cfg), tray_position(cfg)
