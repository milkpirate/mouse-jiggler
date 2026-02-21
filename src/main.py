import asyncio
import sys

import microcontroller
import supervisor
import usb_hid
from adafruit_hid.mouse import Mouse

from config import (
    drive_flag_file,
    jiggle_distance,
    serial_drive_enable_command,
    tickle_interval,
)


class SerialCommandHandler:
    """Handles serial command processing with buffering."""

    def __init__(self, enable_command: str):
        self.enable_command = enable_command
        self.buffer = ""

    async def command_received(self) -> bool:
        """
        Process available serial data.
        Returns True if command matches enable_command.
        """
        available_bytes = supervisor.runtime.serial_bytes_available
        if not available_bytes:
            return False

        chunk = sys.stdin.read(available_bytes)
        if not chunk:
            return False

        self.buffer += chunk.replace("\r", "\n")
        return await self._process_lines()

    async def _process_lines(self) -> bool:
        """Process complete lines in buffer."""
        if "\n" not in self.buffer:
            return False

        line, self.buffer = self.buffer.split("\n", 1)
        command = line.strip()

        if not command:
            return False

        if command == self.enable_command:
            return True

        print("Unknown command: %s" % command)
        print("Available commands: %s" % self.enable_command)

        return False


def min_sec_fmt(duration):
    """Format duration as 'Xmin Ysec'."""
    duration = max(0, duration)  # Ensure non-negative
    mins = int(duration / 60)
    secs = int(duration % 60)
    return "%dmin %dsec" % (mins, secs)


def jiggle(mouse, distance: int = 1):
    """Move mouse by distance and back."""
    mouse.move(x=distance)
    mouse.move(x=-distance)


async def serial_command_handling(handler: SerialCommandHandler, flag_file: str):
    """Task to process serial commands."""
    if not await handler.command_received():
        await asyncio.sleep(0.05)
        return

    print("\n!!! Creating temporary flag file '%s' and rebooting..." % flag_file)
    print("!!! USB storage will be enabled for next boot only!")

    try:
        with open(flag_file, "w") as f:
            f.write("1")
    except Exception as e:
        print("Could not open/create file %s, error: %s" % (flag_file, e))
        return

    await asyncio.sleep(0.5)
    microcontroller.reset()


async def serial_usage_message(enable_command: str):
    """Task to periodically print usage message."""
    print("Send: '%s' - to reboot with temporarily enable USB storage" % enable_command)
    await asyncio.sleep(30)


async def jiggler(mouse, interval: int, distance: int):
    secs_to_go = interval
    print(" "*50, end="\r")

    while secs_to_go:
        print("Next jiggle in %s... " % min_sec_fmt(secs_to_go), end="\r")
        secs_to_go -= 1
        await asyncio.sleep(1)

    print("Next jiggle in %s... " % min_sec_fmt(secs_to_go), end="")
    print("Jiggle jiggle!", end="\r")
    jiggle(mouse, distance)
    await asyncio.sleep(1)


def setup_usb():
    supervisor.set_usb_identification("CPY", "Mouse MJ2040")
    usb_hid.set_interface_name("CPY Mouse MJ2040")


def print_banner(interval: int, distance: int, enable_command: str):
    """Print startup banner."""
    print("Mouse jiggler started!\n")
    print("Interval %s" % min_sec_fmt(interval))
    print("Distance ±%dpx" % distance)
    print(
        "Serial command: '%s' - to reboot with temporarily enable USB storage"
        % enable_command
    )
    print("Enter main loop...\n")


async def run_forever(coro_func, *a, **kw):
    """Run coroutine function forever."""
    while True:
        await coro_func(*a, **kw)
        await asyncio.sleep(0)


async def main():
    mouse = Mouse(usb_hid.devices)
    setup_usb()

    await asyncio.sleep(5)
    print_banner(tickle_interval, jiggle_distance, serial_drive_enable_command)
    handler = SerialCommandHandler(serial_drive_enable_command)

    await asyncio.gather(
        run_forever(serial_usage_message, serial_drive_enable_command),
        run_forever(serial_command_handling, handler, drive_flag_file),
        run_forever(jiggler, mouse, tickle_interval, jiggle_distance)
    )


if __name__ == "__main__":
    asyncio.run(main())
