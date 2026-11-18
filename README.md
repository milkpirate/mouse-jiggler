# Mouse Jiggler
![Tests](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2Fmilkpirate%2Fc2389bbe0a2312450ec9358e81f1b0e8%2Fraw%2F28a36edb66f16a3143a0b162bbfb828ea35ca044%2Fmouse-jiggler-junit-tests.json)
![Coverage](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2Fmilkpirate%2Fc2389bbe0a2312450ec9358e81f1b0e8%2Fraw%2Fmouse-jiggler-cobertura-coverage.json)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
![GitHub License](https://img.shields.io/github/license/milkpirate/mouse-jiggler)

Hardware mouse jiggler based on Raspberry Pi Pico and [CircuitPython](https://circuitpython.org/).

## Features
- Tested on RP2040
- Disabled USB drive mode (no mass storage), can be enabled if needed via button and serial console
- Configurable jiggling interval (default: 5 minutes)
- Configurable jiggling distance (default: move mouse by 1 pixel right and back)
- Configurable drive activation button pin and behavior

## Configuration
All options live in [`settings.toml`] and are read via `supervisor.get_setting()`, so values are typed:
booleans must be written as `true` / `false`, numbers without quotes.

| Setting                       | Type   | Default               | Description                                                        |
|-------------------------------|--------|-----------------------|--------------------------------------------------------------------|
| `enable_drive_by_default`     | bool   | `false`               | Always expose the USB drive (disables the hiding)                  |
| `enable_drive_serial_command` | string | `"enable_usb_reboot"` | Serial command to reboot with the USB drive enabled                |
| `enable_drive_button_pin`     | string | -                     | Board pin of the drive activation button, e.g. `"GP29"`            |
| `button_activation`           | bool   | `false`               | `true` = button is active high, `false` = active low               |
| `led_pin`                     | string | -                     | Board pin of the status LED, e.g. `"GP22"`; omit to run without LED |
| `led_active_low`              | bool   | `false`               | Invert the LED output                                              |
| `tickle_interval`             | int    | `300`                 | Seconds between two jiggles                                        |
| `jiggle_distance`             | int    | `1`                   | Pixels the cursor is moved (and moved back)                        |
| `cpy_drive_location`          | string | -                     | Host only: where the [CircuitPython] drive shows up, e.g. `"F:\\"` |

`cpy_drive_location` is only used by the host tooling (`task upload` etc.) to deploy the firmware to the device.

### Enabling the USB drive
By default, the USB drive is hidden and only the serial console is exposed. To get the drive back for **the next
boot only**, either:
- hold the button while plugging in the device, or
- send the `enable_drive_serial_command` (default: `enable_usb_reboot`) over the serial console - the device reboots
  with the drive enabled, or
- run `task enable_drives`, which does the latter for you (`task upload` does so automatically if the drive is missing).

To keep the drive permanently, set `enable_drive_by_default = true`.

## Hardware
Any [CircuitPython] device with USB HID support should work, but this was only tested on
the [RP2040 development board]. It was flashed with the [CircuitPython] firmware for [Waveshare RP2040-One].
This seemed the best suiting firmware for the board. Though, my development board has just a green LED 
instead of a Neopixel installed, a more colorful indication of the states is not possible.

Requires a [CircuitPython] version providing `supervisor.get_setting()` (tested with 10.3.2). On older versions
`boot.py` fails, which leaves the USB drive enabled.

## Software
The firmware is written in [CircuitPython] and can be easily adapted to other microcontrollers supported by
it. The code is mostly hardware independent, except the pin definitions (and USB HID 
capability) which can be configured in the [`settings.toml`] file.

It starts several asynchronous tasks:
- one for the jiggling
- one banner print to serial console (with a manual how to re-activate the drive mode)
- one for handling this very serial communication / commands

### Requirements
- [`task`](https://taskfile.dev/docs/installation) - modern `make` alternative for building and running tasks.
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) - modern Python environment and package manager.

### Building and flashing
Please consult `task --list` for available tasks.
```bash
task install  # will install the required CircuitPython libraries onto the board
task upload   # will build and flash the firmware to the device
```
[`settings.toml`]: src/settings.toml

[CircuitPython]: https://circuitpython.org/
[RP2040 development board]: https://de.aliexpress.com/item/1005006711101391.html?spm=a2g0o.order_list.order_list_main.11.12d01802GCZ1p2&gatewayAdapt=glo2deu
[Waveshare RP2040-One]: https://circuitpython.org/board/waveshare_rp2040_one/
