import os
import time

import board
import digitalio
import storage
import usb_cdc

from lib.nvm import enable_drive


def boot():
    enable_drive_button_pin = os.getenv("enable_drive_button_pin")
    enable_drive_by_default = bool(os.getenv("enable_drive_by_default", 0))
    button_activation = bool(os.getenv("button_activation", 0))

    if enable_drive_by_default:
        return

    button_pressed = is_button_active(enable_drive_button_pin, button_activation)
    must_enable_drive = button_pressed or enable_drive

    if not must_enable_drive:
        storage.disable_usb_drive()
        usb_cdc.enable(console=True, data=False)

    enable_drive(enable_drive_by_default)


def is_button_active(pin_name: str, button_activation: bool = False) -> bool:
    pin_object = getattr(board, pin_name, None)

    if not pin_object:
        return False

    enable_drive_button = digitalio.DigitalInOut(pin_object)
    enable_drive_button.direction = digitalio.Direction.INPUT   # is already the default
    enable_drive_button.pull = digitalio.Pull.DOWN if button_activation else digitalio.Pull.UP
    time.sleep(1)

    return enable_drive_button.value == button_activation


if __name__ == "__main__":
    boot()
