# Mouse Jiggler
![Tests](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2Fmilkpirate%2Fc2389bbe0a2312450ec9358e81f1b0e8%2Fraw%2F28a36edb66f16a3143a0b162bbfb828ea35ca044%2Fmouse-jiggler-junit-tests.json)
![Coverage](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2Fmilkpirate%2Fc2389bbe0a2312450ec9358e81f1b0e8%2Fraw%2F28a36edb66f16a3143a0b162bbfb828ea35ca044%2Fmouse-jiggler-cobertura-coverage.json)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
![GitHub License](https://img.shields.io/github/license/milkpirate/mouse-jiggler)

Hardware mouse jiggler based on Raspberry Pi Pico and [CircuitPython](https://circuitpython.org/).

## Features
- Tested on RP2040
- Disabled USB drive mode (no mass storage), can be enabled if needed via button and serial console
- Configurable jiggling interval (default: 5 minutes)
- Configurable jiggling pattern (default: move mouse by 1 pixel in left right direction)
- Configurable drive activation button pin and behavior

## Configuration
See [`settings.toml`] for available options. Further one need to configure the location where the [CircuitPython] 
drive shows up on your system. This is required to be able to deploy the firmware to the device.

## Hardware
Any [CircuitPython] device with USB HID support should work, should work, but this one was tested on
this [RP2040 development board]. It was flashed with the [CircuitPython] firmware for [Waveshare RP2040-One].
This seemed the best suiting firmware for the board, but I still could not get the Neopixel LED on this board
to work. This would be a nice addition to indicate the current state of the device, but is not critical for
the functionality.

## Software
The firmware is written in [CircuitPython] and can be easily adapted to other microcontrollers supported by
CircuitPython. The code is mostly hardware independent, except the pin definitions (and USB HID 
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
task setup    # will PlatformIO, require dependencies and the board definitions for nicenano 
task upload   # will build and flash the firmware to the device
```
[`settings.toml`]: src/settings.toml

[CircuitPython]: https://circuitpython.org/
[RP2040 development board]: https://de.aliexpress.com/item/1005006711101391.html?spm=a2g0o.order_list.order_list_main.11.12d01802GCZ1p2&gatewayAdapt=glo2deu
[Waveshare RP2040-One]: https://circuitpython.org/board/waveshare_rp2040_one/
