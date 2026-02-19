import storage
import board
import usb_cdc
import digitalio
import time
import os

from config import drive_flag_file

enable_drive_button = digitalio.DigitalInOut(board.GP28)
enable_drive_button.pull = digitalio.Pull.UP
time.sleep(1)

enable_drive_button_pressed = not enable_drive_button.value
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