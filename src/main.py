import asyncio
import os
import sys

import microcontroller
import supervisor
import usb_hid
from adafruit_hid.mouse import Mouse


class SerialCommandHandler:
    """Handles serial command processing."""

    def __init__(self, enable_command: str):
        self.enable_command = enable_command
        self.buffer = b""

    def _fill_buffer(self):
        if not (available_bytes := supervisor.runtime.serial_bytes_available):
            return False

        if not (chunk := sys.stdin.read(available_bytes)):
            return False

        if isinstance(chunk, str):
            chunk = chunk.encode()

        self.buffer += chunk
        return True

    def _extract_first_complete_line(self):
        """Extract a line from buffer if available."""
        if not self.buffer:
            return None

        if b"\n" not in self.buffer:
            return None

        line, self.buffer = self.buffer.split(b"\n", 1)
        return line.decode().strip()

    async def command_received(self) -> bool:
        """Process available serial data. Returns True if command matches enable_command."""
        if not self._fill_buffer():
            await asyncio.sleep(0.001)
            return False

        line = self._extract_first_complete_line()
        if line is None:
            return False

        if line == self.enable_command:
            return True

        print(f"Unknown command: {line!r}")
        print(f"Available commands: {self.enable_command!r}")
        return False


def min_sec_fmt(duration):
    """Format duration as 'Xmin Ysec'."""
    duration = max(0, duration)  # Ensure non-negative
    mins = int(duration / 60)
    secs = int(duration % 60)
    return f"{mins}min {secs}sec"


def jiggle(mouse, distance: int = 1):
    """Move mouse by distance and back."""
    mouse.move(x=distance)
    mouse.move(x=-distance)


async def serial_command_handling(handler: SerialCommandHandler, flag_file: str):
    """Task to process serial commands."""
    if not await handler.command_received():
        await asyncio.sleep(0.05)
        return

    print(f"\n!!! Creating temporary flag file {flag_file!r} and rebooting...")
    print("!!! USB storage will be enabled for next boot only!")

    try:
        with open(flag_file, "w") as f:
            f.write("1")
    except Exception as e:
        print(f"Could not open/create file {flag_file}, error: {e}")
        return

    await asyncio.sleep(0.5)
    microcontroller.reset()


async def serial_usage_message(enable_command: str):
    """Task to periodically print usage message."""
    print(f"Send: {enable_command!r} - to reboot with temporarily enable USB storage")
    await asyncio.sleep(30)


async def jiggler(mouse, interval: int, distance: int):
    secs_to_go = interval
    print(" "*50, end="\r")

    while secs_to_go:
        print(f"Next jiggle in {min_sec_fmt(secs_to_go)}... ", end="\r")
        secs_to_go -= 1
        await asyncio.sleep(1)

    print(f"Next jiggle in {min_sec_fmt(secs_to_go)}... ", end="")
    print("Jiggle jiggle!", end="\r")
    jiggle(mouse, distance)
    await asyncio.sleep(1)


def setup_usb():
    supervisor.set_usb_identification("CPY", "Mouse MJ2040")
    usb_hid.set_interface_name("CPY Mouse MJ2040")


def print_banner(interval: int, distance: int, enable_command: str):
    """Print startup banner."""
    print("Mouse jiggler started!\n")
    print(f"Interval {min_sec_fmt(interval)}")
    print(f"Distance ±{distance}px")
    print(f"Serial command: {enable_command!r} - to reboot with temporarily enable USB storage")
    print("Enter main loop...\n")


async def run_forever(coro_func, *a, **kw):
    """Run coroutine function forever."""
    while True:
        await coro_func(*a, **kw)
        await asyncio.sleep(0)


async def main():
    mouse = Mouse(usb_hid.devices)
    setup_usb()

    tickle_interval = os.getenv("tickle_interval")
    jiggle_distance = os.getenv("jiggle_distance")
    enable_drive_flag_file = os.getenv("enable_drive_flag_file")
    enable_drive_serial_command = os.getenv("enable_drive_serial_command")

    await asyncio.sleep(5)
    print_banner(tickle_interval, jiggle_distance, enable_drive_serial_command)
    handler = SerialCommandHandler(enable_drive_serial_command)

    await asyncio.gather(
        run_forever(serial_usage_message, enable_drive_serial_command),
        run_forever(serial_command_handling, handler, enable_drive_flag_file),
        run_forever(jiggler, mouse, tickle_interval, jiggle_distance)
    )


if __name__ == "__main__":
    asyncio.run(main())
