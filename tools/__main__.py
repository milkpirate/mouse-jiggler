"""
Tools

Usage:
  tool enable_drive
  tool setting <key>
  tool -h | --help
  tool -v | --version

Options:
  -h --help     Show this screen.
  --version     Show version.
"""

import pathlib
import sys

import docopt
import serial
import toml

self = pathlib.Path(__file__)
sys.path.append(self.parent.parent.__str__())
settings_file = self.parent.parent / "src/settings.toml"


def main(argv):
    opts = docopt.docopt(__doc__, argv)

    if opts["setting"]:
        key = opts["<key>"]
        value = get_setting(key)
        print(value)
        return

    if opts["enable_drive"]:
        enable_drive_serial_command = get_setting("enable_drive_serial_command")
        cyp_serial_port = get_setting("cyp_serial_port")

        with serial.Serial(cyp_serial_port, 115200) as com:
            com.write(f"{enable_drive_serial_command}\n".encode())


def get_setting(key: str, default: any =None):
    settings_content = settings_file.read_text()
    settings = toml.loads(settings_content)

    if not (value := settings.get(key, default)):
        raise ValueError(f"Setting '{key}' not found in settings.toml")

    return value


if __name__ == "__main__":
    main(sys.argv[1:])
