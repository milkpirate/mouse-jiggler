import time
import struct

class Gamepad:
    """Emulate a generic gamepad controller with 16 buttons,
    numbered 1-16, and two joysticks, one controlling
    ``x` and ``y`` values, and the other controlling ``z`` and
    ``r_z`` (z rotation or ``Rz``) values.

    The joystick values could be interpreted
    differently by the receiving program: those are just the names used here.
    The joystick values are in the range -127 to 127."""

    def __init__(self, devices):
        """Create a Gamepad object that will send USB gamepad HID reports.

        Devices can be a list of devices that includes a gamepad device or a gamepad device
        itself. A device is any object that implements ``send_report()``, ``usage_page`` and
        ``usage``.
        """
        self._gamepad_device = devices

        # Reuse this bytearray to send mouse reports.
        # Typically, controllers start numbering buttons at 1 rather than 0.
        # report[0] buttons 1-8 (LSB is button 1)
        # report[1] buttons 9-16
        # report[2] joystick 0 x: -127 to 127
        # report[3] joystick 0 y: -127 to 127
        # report[4] joystick 1 x: -127 to 127
        # report[5] joystick 1 y: -127 to 127
        self._report = bytearray(6)

        # Remember the last report as well, so we can avoid sending
        # duplicate reports.
        self._last_report = bytearray(6)

        # Store settings separately before putting into report. Saves code
        # especially for buttons.
        self._buttons_state = 0
        self._joy_x = 0
        self._joy_y = 0
        # self._joy_z = 0
        # self._joy_r_z = 0

        # Send an initial report to test if HID device is ready.
        # If not, wait a bit and try once more.
        try:
            self.reset_all()
        except OSError:
            time.sleep(1)
            self.reset_all()

    def parse_raw(self, raw: bytearray):
        self._buttons_state = (raw[0] & 0xf0) | ((raw[1] & 0x0f) << 4)
        dirs = (raw[0] >> 4) & 0x0f

        # Up(1) - Down(2) results in 1, 0, or -1
        self._joy_y = (( dirs &  1) -      ((dirs >> 1) & 1)) * 127
        # Right(8) - Left(4) results in 1, 0, or -1
        self._joy_x = (((dirs >> 3) & 1) - ((dirs >> 2) & 1)) * 127

        # self._joy_z = 0
        # self._joy_r_z = 0

    def reset_all(self):
        """Release all buttons and set joysticks to zero."""
        self._buttons_state = 0
        self._joy_x = 0
        self._joy_y = 0
        # self._joy_z = 0
        # self._joy_r_z = 0
        self.send(always=True)

    def send(self, always=False):
        """Send a report with all the existing settings.
        If ``always`` is ``False`` (the default), send only if there have been changes.
        """
        struct.pack_into(
            "<Hbbbb",
            self._report,
            0,
            self._buttons_state,
            self._joy_x,
            self._joy_y,
            0, # self._joy_z,
            0, # self._joy_r_z,
        )

        if always or self._last_report != self._report:
            self._gamepad_device.send_report(self._report)
            # Remember what we sent, without allocating new storage.
            self._last_report[:] = self._report
