import time

import board
import digitalio
import storage
import supervisor
import usb_cdc

from lib.nvm import enable_drive


def boot():
    enable_drive_button_pin = supervisor.get_setting("enable_drive_button_pin")
    enable_drive_by_default = supervisor.get_setting("enable_drive_by_default", False)
    button_activation = supervisor.get_setting("button_activation", False)

    drive_requested = bool(enable_drive)
    enable_drive(False)  # one-shot flag, always consume it

    if enable_drive_by_default:
        return

    if not (is_button_active(enable_drive_button_pin, button_activation) or drive_requested):
        storage.disable_usb_drive()
        usb_cdc.enable(console=True, data=False)


def is_button_active(pin_name: str, button_activation: bool = False) -> bool:
    pin_object = getattr(board, pin_name, None) if pin_name else None

    if not pin_object:
        return False

    enable_drive_button = digitalio.DigitalInOut(pin_object)
    enable_drive_button.direction = digitalio.Direction.INPUT   # is already the default
    enable_drive_button.pull = digitalio.Pull.DOWN if button_activation else digitalio.Pull.UP
    time.sleep(1)

    return enable_drive_button.value == button_activation


if __name__ == "__main__":
    boot()
