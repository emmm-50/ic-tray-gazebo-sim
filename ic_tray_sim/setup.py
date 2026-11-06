from setuptools import find_packages, setup
from glob import glob

setup(name='ic_tray_sim', version='0.1.0', packages=find_packages(),
      data_files=[('share/ament_index/resource_index/packages', ['resource/ic_tray_sim']),
                  ('share/ic_tray_sim', ['package.xml']),
                  ('share/ic_tray_sim/launch', glob('launch/*.launch.py')),
                  ('share/ic_tray_sim/config', glob('config/*.yaml'))],
      install_requires=['setuptools'], zip_safe=True,
      entry_points={'console_scripts': ['pick_place = ic_tray_sim.pick_place:main']})
