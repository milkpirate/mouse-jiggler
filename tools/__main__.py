"""
Tools

Usage:
  tool enable_drives
  tool setting <key>
  tool -h | --help
  tool -v | --version

Options:
  -h --help     Show this screen.
  --version     Show version.
"""

import pathlib
import sys
from types import SimpleNamespace

import docopt
import serial
import toml
from serial.tools.list_ports import comports
from serial.tools.list_ports_common import ListPortInfo

self = pathlib.Path(__file__)
sys.path.append(self.parent.parent.__str__())
settings_file = self.parent.parent / "src/settings.toml"


cyp = SimpleNamespace(
    vid=0x2e8a,
    pid=0x103a,
)


def main(argv):
    opts = docopt.docopt(__doc__, argv)

    if opts["setting"]:
        key = opts["<key>"]
        value = get_setting(key)
        print(value)
        return

    if opts["enable_drives"]:
        enable_drive_serial_command = get_setting("enable_drive_serial_command")

        for port in get_cpy_serial_ports():
            with serial.Serial(port.device, 115200) as com:
                com.write(f"{enable_drive_serial_command}\n".encode())


def get_cpy_serial_ports():
    return find_serial_port(vid=cyp.vid, pid=cyp.pid)


def find_serial_port(vid, pid) -> list[ListPortInfo]:
    return [
        p for p in comports()
            if p.vid == vid
           and p.pid == pid
    ]


def get_setting(key: str, default: any =None):
    settings_content = settings_file.read_text()
    settings = toml.loads(settings_content)

    if not (value := settings.get(key, default)):
        raise ValueError(f"Setting '{key}' not found in settings.toml")

    return value


if __name__ == "__main__":
    main(sys.argv[1:])
