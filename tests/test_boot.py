import pytest

from src.config import button_pin


@pytest.mark.parametrize(
    "button_pressed, active_low, drive_files, list_error, rm_error, disable_drive",
    [
        # test_boot_regular
        (False, True, [], None, None, True),
        # test_boot_button_pressed
        (True, True, ["foo"], None, None, False),
        # active high button pressed
        (False, False, ["foo"], None, None, False),
        # test_boot_file_exists
        (False, True, ["bar", "usb_drive.enable"], None, None, False),
        # test_boot_file_exists_and_buttons_pressed
        (True, True, ["bar", "usb_drive.enable"], None, None, False),
        # test_boot_list_err
        (False, True, ["bar", "usb_drive.enable"], OSError("list err"), None, True),
        # test_boot_rm_err
        (False, True, ["bar", "usb_drive.enable"], None, OSError("rm err"), False),
    ],
)
def test_boot(circuit_python_mocks, active_low, button_pressed, drive_files, list_error, rm_error, disable_drive):
    circuit_python_mocks.digitalio.DigitalInOut.return_value.value = button_pressed ^ active_low
    circuit_python_mocks.os.listdir.return_value = drive_files
    circuit_python_mocks.os.listdir.side_effect = list_error
    circuit_python_mocks.os.remove.side_effect = rm_error

    from boot import boot
    boot()

    circuit_python_mocks.digitalio.DigitalInOut.assert_called_once_with(button_pin)
    button_instance = circuit_python_mocks.digitalio.DigitalInOut.return_value
    assert button_instance.pull == circuit_python_mocks.digitalio.Pull.UP \
        if active_low else circuit_python_mocks.digitalio.Pull.DOWN
    circuit_python_mocks.time.sleep.assert_called_once_with(1)
    circuit_python_mocks.os.listdir.assert_called_once_with("/")

    if disable_drive:
        circuit_python_mocks.storage.disable_usb_drive.assert_called_once()
        circuit_python_mocks.usb_cdc.enable.assert_called_once_with(console=True, data=False)
    else:
        circuit_python_mocks.usb_cdc.enable.assert_not_called()
        circuit_python_mocks.storage.disable_usb_drive.assert_not_called()
