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

def get_setting(key: str, default: any =None):
    settings_content = settings_file.read_text()
    settings = toml.loads(settings_content)
    return settings.get(key, default)

def main(argv):
    opts = docopt.docopt(__doc__, argv)

    if opts["setting"]:
        key = opts["<key>"]
        value = get_setting(key)
        print(value)
        return

    if opts["enable_drive"]:
        serial_drive_enable_command = get_setting("serial_drive_enable_command")
        with serial.Serial("COM15", 115200) as com:
            com.write(f"{serial_drive_enable_command}\n".encode())

if __name__ == "__main__":
    main(sys.argv[1:])
