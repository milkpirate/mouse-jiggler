import storage
import usb_cdc
import digitalio
import time
import os

from config import (
    drive_flag_file,
    button_pin,
    button_active_low,
)


def boot():
    enable_drive_button = digitalio.DigitalInOut(button_pin)
    enable_drive_button.pull = digitalio.Pull.UP if button_active_low else digitalio.Pull.DOWN
    time.sleep(1)

    enable_drive_button_pressed = enable_drive_button.value ^ button_active_low
    enable_drive_file_exists = False


    try:
        enable_drive_file_exists = drive_flag_file in os.listdir("/")
        os.remove(drive_flag_file)
    except:
        pass

    disable_drive = not (enable_drive_button_pressed or enable_drive_file_exists)

    if disable_drive:
        storage.disable_usb_drive()
        usb_cdc.enable(console=True, data=False)


if __name__ == "__main__":
    boot()
