#!/usr/bin/env python3
"""Terminal keyboard or SDL2 game controller to ROS 2 Twist."""
import argparse
import ctypes
import ctypes.util
import select
import sys
import termios
import time
import tty

import rclpy
from rclpy.signals import SignalHandlerOptions
from geometry_msgs.msg import Twist


def publish(publisher, linear=0.0, angular=0.0):
    msg = Twist()
    msg.linear.x = linear
    msg.angular.z = angular
    publisher.publish(msg)


def keyboard(publisher, linear_speed, angular_speed):
    if not sys.stdin.isatty():
        raise RuntimeError('键盘遥控需要交互式终端。')
    settings = termios.tcgetattr(sys.stdin)
    # A held key repeats on most terminals; release stops after the timeout.
    timeout = 0.3
    command = (0.0, 0.0)
    last_input = 0.0
    keys = {'w': (linear_speed, 0.0), 's': (-linear_speed, 0.0),
            'a': (0.0, angular_speed), 'd': (0.0, -angular_speed),
            ' ': (0.0, 0.0)}
    print('W/S 前进/后退，A/D 左转/右转，空格停车，Q 退出；松键后自动停车。', flush=True)
    try:
        tty.setcbreak(sys.stdin.fileno())
        while rclpy.ok():
            if select.select([sys.stdin], [], [], 0.05)[0]:
                key = sys.stdin.read(1).lower()
                if key == 'q':
                    break
                if key in keys:
                    command = keys[key]
                    last_input = time.monotonic()
            if time.monotonic() - last_input > timeout:
                command = (0.0, 0.0)
            publish(publisher, *command)
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)


def xbox(publisher, linear_speed, angular_speed, device):
    library = ctypes.util.find_library('SDL2') or 'libSDL2-2.0.so.0'
    try:
        sdl = ctypes.CDLL(library)
    except OSError as exc:
        raise RuntimeError(f'无法加载 SDL2: {exc}') from exc
    sdl.SDL_Init.argtypes = [ctypes.c_uint32]
    sdl.SDL_Init.restype = ctypes.c_int
    sdl.SDL_GetError.restype = ctypes.c_char_p
    sdl.SDL_NumJoysticks.restype = ctypes.c_int
    sdl.SDL_IsGameController.argtypes = [ctypes.c_int]
    sdl.SDL_IsGameController.restype = ctypes.c_int
    sdl.SDL_GameControllerOpen.argtypes = [ctypes.c_int]
    sdl.SDL_GameControllerOpen.restype = ctypes.c_void_p
    sdl.SDL_GameControllerGetAttached.argtypes = [ctypes.c_void_p]
    sdl.SDL_GameControllerGetAttached.restype = ctypes.c_int
    sdl.SDL_GameControllerGetAxis.argtypes = [ctypes.c_void_p, ctypes.c_int]
    sdl.SDL_GameControllerGetAxis.restype = ctypes.c_int16
    sdl.SDL_GameControllerGetButton.argtypes = [ctypes.c_void_p, ctypes.c_int]
    sdl.SDL_GameControllerGetButton.restype = ctypes.c_uint8
    sdl.SDL_GameControllerClose.argtypes = [ctypes.c_void_p]
    if sdl.SDL_Init(0x00002000) != 0:  # SDL_INIT_GAMECONTROLLER
        raise RuntimeError(f'SDL2 初始化失败: {sdl.SDL_GetError().decode(errors="replace")}')
    controller = None
    try:
        candidates = [device] if device is not None else range(sdl.SDL_NumJoysticks())
        for index in candidates:
            if 0 <= index < sdl.SDL_NumJoysticks() and sdl.SDL_IsGameController(index):
                controller = sdl.SDL_GameControllerOpen(index)
                if controller:
                    break
        if not controller:
            raise RuntimeError('未找到受 SDL2 支持的手柄；请连接手柄后重试。')
        print(f'手柄 {index}：按住 LB 使能，左摇杆前后移动，右摇杆左右转向；Ctrl+C 退出。', flush=True)
        while rclpy.ok() and sdl.SDL_GameControllerGetAttached(controller):
            sdl.SDL_GameControllerUpdate()
            if not sdl.SDL_GameControllerGetAttached(controller):
                break
            if sdl.SDL_GameControllerGetButton(controller, 9):  # LEFTSHOULDER
                forward = -sdl.SDL_GameControllerGetAxis(controller, 1) / 32768.0
                turn = -sdl.SDL_GameControllerGetAxis(controller, 2) / 32768.0
                # Suppress stick drift, preserving the remaining proportional range.
                def axis(value):
                    magnitude = min(abs(value), 1.0)
                    return 0.0 if magnitude <= 0.15 else (1 if value > 0 else -1) * (magnitude - 0.15) / 0.85
                publish(publisher, linear_speed * axis(forward), angular_speed * axis(turn))
            else:
                publish(publisher)
            time.sleep(0.05)
        if rclpy.ok():
            print('手柄已断开，停车。', file=sys.stderr, flush=True)
    finally:
        if controller:
            sdl.SDL_GameControllerClose(controller)
        sdl.SDL_Quit()


def main():
    parser = argparse.ArgumentParser(description='模拟车键盘或 Xbox 手柄遥控，发布 /cmd_vel。')
    parser.add_argument('mode', choices=['keyboard', 'xbox'])
    parser.add_argument('--linear', type=float, default=0.2, help='最大线速度，m/s（默认 0.2）')
    parser.add_argument('--angular', type=float, default=0.5, help='最大角速度，rad/s（默认 0.5）')
    parser.add_argument('--device', type=int, help='SDL 手柄设备索引（默认使用首个支持的手柄）')
    args = parser.parse_args()
    if not (0 < args.linear < float('inf') and 0 < args.angular < float('inf')):
        parser.error('速度必须是正的有限数值。')
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    node = rclpy.create_node('mobile_workcell_teleop')
    publisher = node.create_publisher(Twist, '/cmd_vel', 10)
    try:
        if args.mode == 'keyboard':
            keyboard(publisher, args.linear, args.angular)
        else:
            xbox(publisher, args.linear, args.angular, args.device)
    except KeyboardInterrupt:
        pass
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 1
    finally:
        for _ in range(3):
            publish(publisher)
            time.sleep(0.05)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    return 0


if __name__ == '__main__':
    sys.exit(main())
