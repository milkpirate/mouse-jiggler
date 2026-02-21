import os
import time

import board
import digitalio
import storage
import usb_cdc

from config import (
    button_active_low,
    button_pin,
    drive_flag_file,
)


def boot():
    button_pin_object = getattr(board, button_pin, None)
    button_value = not button_active_low

    if button_pin_object:
        enable_drive_button = digitalio.DigitalInOut(button_pin)
        enable_drive_button.pull = digitalio.Pull.UP if button_active_low else digitalio.Pull.DOWN
        time.sleep(1)
        button_value = enable_drive_button.value

    enable_drive_button_pressed = button_value ^ button_active_low
    enable_drive_file_exists = False

    try:
        enable_drive_file_exists = drive_flag_file in os.listdir("/")
        os.remove(drive_flag_file)
    except: # noqa: E722
        pass

    disable_drive = not (enable_drive_button_pressed or enable_drive_file_exists)

    if disable_drive:
        storage.disable_usb_drive()
        usb_cdc.enable(console=True, data=False)


if __name__ == "__main__":
    boot()
