import storage
import board
import usb_cdc
import digitalio
import time

drive_button = digitalio.DigitalInOut(board.D10)
drive_button.pull = digitalio.Pull.DOWN
time.sleep(2)

if not drive_button.value:
    storage.disable_usb_drive()
    usb_cdc.enable(console=True, data=False)
