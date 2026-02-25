import os
import time

import board
import digitalio
import storage
import usb_cdc


def boot():
    flag_file = os.getenv("enable_drive_flag_file")
    enable_drive_button_pin = os.getenv("enable_drive_button_pin")
    disable_drive_by_default = bool(os.getenv("disable_drive_by_default", 0))
    button_activation = bool(os.getenv("button_activation", 0))

    if not disable_drive_by_default:
        return

    flag_file_exists = file_exists(flag_file)
    button_pressed = is_button_active(enable_drive_button_pin, button_activation)

    if flag_file_exists:
        try:
            os.remove(flag_file)
        except: # noqa: E722
            pass

    enable_drive = button_pressed or flag_file_exists
    if not enable_drive:
        storage.disable_usb_drive()
        usb_cdc.enable(console=True, data=False)


def is_button_active(pin_name: str, button_activation: bool = False) -> bool:
    pin_object = getattr(board, pin_name, None)

    if not pin_object:
        return False

    enable_drive_button = digitalio.DigitalInOut(pin_object)
    enable_drive_button.pull = digitalio.Pull.DOWN if button_activation else digitalio.Pull.UP
    time.sleep(1)

    return enable_drive_button.value == button_activation


def file_exists(path: str) -> bool:
    if not path:
        return False

    try:
        return path in os.listdir("/")
    except: # noqa: E722
        return False


if __name__ == "__main__":
    boot()
