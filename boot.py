import storage
import board
import usb_cdc
import digitalio
import time

disable_drive = digitalio.DigitalInOut(board.GP28)
disable_drive.pull = digitalio.Pull.UP
time.sleep(1)

if disable_drive.value:
    storage.disable_usb_drive()
    usb_cdc.enable(console=True, data=False)