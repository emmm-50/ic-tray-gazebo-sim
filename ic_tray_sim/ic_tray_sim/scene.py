"""Build a simple SDF world and a simulation-only URDF copy at launch time."""
from pathlib import Path
import xml.etree.ElementTree as ET
from .kinematics import JOINTS, TOOL_Z0, solve

A_MOUNT = (-2.48, -1.20, .25)
A_TRAY_XY = (-2.91, -1.20)


def tray_position(cfg):
    pickup = cfg['pickup']
    if cfg.get('mode') == 'a_pickup':
        return [*A_TRAY_XY, A_MOUNT[2] + pickup['surface'] + cfg['tray']['size'][2] / 2]
    return [pickup['x'], pickup['y'], pickup['surface'] + cfg['tray']['size'][2] / 2]


def box(name, pose, size, color, static=True, mass=None, collision=True):
    x, y, z = size
    inertia = ''
    if mass is not None:
        ixx = mass * (y*y + z*z) / 12
        iyy = mass * (x*x + z*z) / 12
        izz = mass * (x*x + y*y) / 12
        inertia = f'<inertial><mass>{mass}</mass><inertia><ixx>{ixx}</ixx><iyy>{iyy}</iyy><izz>{izz}</izz></inertia></inertial>'
    geometry = f'<geometry><box><size>{x} {y} {z}</size></box></geometry>'
    collision_xml = f'<collision name="collision">{geometry}</collision>' if collision else ''
    return f'''<model name="{name}"><static>{str(static).lower()}</static><pose>{pose[0]} {pose[1]} {pose[2]} 0 0 0</pose>
      <link name="body">{inertia}{collision_xml}
      <visual name="visual">{geometry}<material><ambient>{color}</ambient><diffuse>{color}</diffuse></material></visual></link></model>'''


def world(cfg):
    pickup = cfg['pickup']
    if cfg.get('mode') == 'a_pickup':
        # Simplified collision solids at the layout's actual A-dock dimensions.
        x, y, z = tray_position(cfg)
        surface = z - cfg['tray']['size'][2] / 2
        items = [box('ground', [-2.5, -1.2, -.025], [3, 3, .05], '.75 .75 .75 1'),
                 box('vehicle', [-2.30, -1.20, .125], [.7, .5, .25], '.18 .2 .22 1'),
                 box('conveyor', [x, y, surface - .025], [.18, .65, .05], '.18 .2 .55 1')]
        return world_sdf(items)
    shelf = cfg['shelf']
    # Static conveyor, resized from the structure of the official example:
    # https://github.com/gazebosim/gz-sim/blob/gz-sim8/examples/worlds/conveyor.sdf
    belt_size = cfg['conveyor']['size']
    items = [box('ground', [0, 0, -0.025], [3, 3, .05], '.75 .75 .75 1'),
             box('conveyor', [pickup['x'], pickup['y'], pickup['surface']-belt_size[2]/2], belt_size, '.18 .2 .22 1')]
    # Lower level is a solid plate. Two upper beams span the configured slots,
    # supporting the tray while leaving clearance for the arm below.
    low, high = shelf['levels']
    items.append(box('shelf_lower', [shelf['x'], shelf['y'], low-shelf['thickness']/2],
                     [shelf['depth'], shelf['slots']*shelf['slot_spacing'], shelf['thickness']], '.5 .5 .55 1'))
    for i, offset in enumerate((-.045, .075)):
        items.append(box(f'upper_beam_{i}',
                         [shelf['x'] + offset, shelf['y'], high-shelf['thickness']/2],
                         [.02, shelf['slots']*shelf['slot_spacing'], shelf['thickness']], '.5 .5 .55 1'))
    # Visual slot outlines in a horizontal plane mark the configured positions.
    for j in range(shelf['slots'] + 1):
        y = shelf['y'] + (j - shelf['slots']/2) * shelf['slot_spacing']
        items.append(box(f'slot_mark_{j}', [shelf['x'], y, high],
                         [shelf['depth'], .002, .001], '.9 .9 .9 1', collision=False))
    return world_sdf(items)


def world_sdf(items):
    return '''<?xml version="1.0"?><sdf version="1.9"><world name="ic_tray">
      <gravity>0 0 -9.81</gravity><physics name="physics" type="ignored"><max_step_size>0.001</max_step_size><real_time_factor>1</real_time_factor></physics>
      <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
      <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
      <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
      <light name="sun" type="directional"><pose>0 0 5 0 0 0</pose><diffuse>0.8 0.8 0.8 1</diffuse><direction>-0.5 0.2 -1</direction></light>''' + ''.join(items) + '</world></sdf>'


def tray_sdf(cfg):
    tray = cfg['tray']
    size = tray['size']
    model = box('tray', [0, 0, 0],
                size, '.15 .25 .65 1', False, tray['mass'])
    return '<sdf version="1.9">' + model + '</sdf>'


def robot_xml(description_dir, controllers, cfg):
    root = ET.parse(Path(description_dir) / 'urdf/prrr_arm.urdf').getroot()
    for mesh in root.iter('mesh'):
        mesh.set('filename', str(Path(description_dir) / 'meshes' / Path(mesh.get('filename')).name))
    # These conservative values exist only in this generated simulation model.
    for joint in root.findall('joint'):
        if joint.get('name') == 'lift_joint':
            joint.find('limit').set('effort', '100'); joint.find('limit').set('velocity', '0.2')
        elif joint.get('name') in JOINTS[1:]:
            ET.SubElement(joint, 'limit', {'effort': '20', 'velocity': '1.0'})
    ET.SubElement(root, 'link', {'name': 'world'})
    fix = ET.SubElement(root, 'joint', {'name': 'world_fixed', 'type': 'fixed'})
    ET.SubElement(fix, 'parent', {'link': 'world'}); ET.SubElement(fix, 'child', {'link': 'base_footprint'})
    if cfg.get('mode') == 'a_pickup':
        ET.SubElement(fix, 'origin', {'xyz': ' '.join(str(v) for v in A_MOUNT), 'rpy': '0 0 3.141592653589793'})
    control = ET.SubElement(root, 'ros2_control', {'name': 'GazeboSimSystem', 'type': 'system'})
    hardware = ET.SubElement(control, 'hardware'); ET.SubElement(hardware, 'plugin').text = 'gz_ros2_control/GazeboSimSystem'
    pick = cfg['pickup']; z = TOOL_Z0 + cfg['travel_lift']
    initial = solve(pick['x'], pick['y'], z)
    for name, value in zip(JOINTS, initial):
        joint = ET.SubElement(control, 'joint', {'name': name})
        ET.SubElement(joint, 'command_interface', {'name': 'position'})
        pos = ET.SubElement(joint, 'state_interface', {'name': 'position'})
        ET.SubElement(pos, 'param', {'name': 'initial_value'}).text = str(value)
        ET.SubElement(joint, 'state_interface', {'name': 'velocity'})
    gazebo = ET.SubElement(root, 'gazebo')
    plugin = ET.SubElement(gazebo, 'plugin', {'filename': 'libgz_ros2_control-system.so', 'name': 'gz_ros2_control::GazeboSimROS2ControlPlugin'})
    ET.SubElement(plugin, 'parameters').text = str(controllers)
    detachable = ET.SubElement(gazebo, 'plugin', {'filename': 'gz-sim-detachable-joint-system', 'name': 'gz::sim::systems::DetachableJoint'})
    for key, value in [('parent_link', 'wrist_link'), ('child_model', 'tray'), ('child_link', 'body'),
                       ('detach_topic', '/suction/detach'), ('attach_topic', '/suction/attach'), ('output_topic', '/suction/state')]:
        ET.SubElement(detachable, key).text = value
    return ET.tostring(root, encoding='unicode')
