import usb_hid
import supervisor
import microcontroller
import sys
import asyncio

from config import (
    drive_flag_file,
    serial_drive_enable_command
)
from adafruit_hid.mouse import Mouse

tickle_interval = 5 * 60  # 5min
jiggle_distance = 1
_serial_buffer = ""


async def main():
    mouse = Mouse(usb_hid.devices)
    setup_usb()

    await asyncio.sleep(5)
    print_banner()

    asyncio.create_task(serial_command_task())
    asyncio.create_task(serial_usage_message_task())

    await jiggle_task(mouse)


def setup_usb():
    supervisor.set_usb_identification("CPY", "Mouse MJ2040")
    usb_hid.set_interface_name("CPY Mouse MJ2040")


def print_banner():
    print("Mouse jiggler started!\n")
    print("Interval %s" % min_sec_fmt(tickle_interval))
    print("Distance ±%dpx" % jiggle_distance)
    print(
        "Serial command: '%s' - to reboot with temporarily enable USB storage"
        % serial_drive_enable_command
    )
    print("Enter main loop...\n")


async def serial_command_task():
    global _serial_buffer

    while True:
        available_bytes = supervisor.runtime.serial_bytes_available
        if not available_bytes:
            await asyncio.sleep(0.05)
            continue

        chunk = sys.stdin.read(available_bytes)
        if not chunk:
            await asyncio.sleep(0)  # balance task fairness
            continue

        _serial_buffer += chunk.replace("\r", "\n")
        while "\n" in _serial_buffer:
            line, _serial_buffer = _serial_buffer.split("\n", 1)
            command = line.strip()

            if not command:
                await asyncio.sleep(0)  # balance task fairness
                continue

            if command == serial_drive_enable_command:
                print("\n!!! Creating temporary flag file '%s' and rebooting..." % drive_flag_file)
                print("!!! USB storage will be enabled for next boot only!")

                try:
                    with open(drive_flag_file, "w") as f:
                        f.write("1")
                except Exception as e:
                    print("Could not open/create file %s, error: %s" % (drive_flag_file, e))
                    continue

                await asyncio.sleep(0.5)
                microcontroller.reset()
                return

            print("Unknown command: %s" % command)
            print("Available commands: %s" % serial_drive_enable_command)


async def serial_usage_message_task():
    while True:
        print(
            "Send: '%s' - to reboot with temporarily enable USB storage"
            % serial_drive_enable_command
        )
        await asyncio.sleep(30)


async def jiggle_task(mouse):
    while True:
        secs_to_go = tickle_interval
        print(" "*50, end="\r")

        while secs_to_go:
            print("Next jiggle in %s... " % min_sec_fmt(secs_to_go), end="\r")
            secs_to_go -= 1
            await asyncio.sleep(1)

        print("Next jiggle in %s... " % min_sec_fmt(secs_to_go), end="")
        print("Jiggle jiggle!", end="\r")
        jiggle(mouse, jiggle_distance)
        await asyncio.sleep(1)


def min_sec_fmt(duration):
    mins = duration/60
    secs = duration%60
    return "%dmin %dsec" % (mins, secs)


def jiggle(mouse, distance=1):
    mouse.move(x=distance)
    mouse.move(x=-distance)


asyncio.run(main())
