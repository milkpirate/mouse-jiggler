import board

drive_flag_file="usb_drive.enable"
serial_drive_enable_command="enable_usb_reboot"
button_pin = board.GP28
button_active_low = True
tickle_interval = 5 * 60  # 5 minutes
jiggle_distance = 1 # px
circuit_python_drive_location = "E:\\"
