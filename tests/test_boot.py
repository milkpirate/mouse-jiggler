import pytest
import sys
import importlib

from config import drive_flag_file


@pytest.mark.parametrize(
    "button_pressed, drive_files, list_error, rm_error, disable_drive",
    [
        # test_boot_regular
        (False, [], None, None, True),
        # test_boot_button_pressed
        (True, ["foo"], None, None, False),
        # test_boot_file_exists
        (False, ["bar", drive_flag_file], None, None, False),
        # test_boot_file_exists_and_buttons_pressed
        (True, ["bar", drive_flag_file], None, None, False),
        # test_boot_list_err
        (False, ["bar", drive_flag_file], OSError("list err"), None, True),
        # test_boot_rm_err
        (False, ["bar", drive_flag_file], None, OSError("rm err"), False),
    ],
)
def test_boot(boot_mocks, button_pressed, drive_files, list_error, rm_error, disable_drive):
    boot_mocks.digitalio.DigitalInOut.return_value.value = not button_pressed
    boot_mocks.os.listdir.return_value = drive_files
    boot_mocks.os.listdir.side_effect = list_error
    boot_mocks.os.remove.side_effect = rm_error

    # ensure a fresh execute of boot.py for each test case
    if 'src.boot' in sys.modules:
        importlib.reload(sys.modules['src.boot'])
    else:
        import src.boot

    boot_mocks.digitalio.DigitalInOut.assert_called_once_with(boot_mocks.board.GP28)
    button_instance = boot_mocks.digitalio.DigitalInOut.return_value
    assert button_instance.pull == boot_mocks.digitalio.Pull.UP
    boot_mocks.time.sleep.assert_called_once_with(1)
    boot_mocks.os.listdir.assert_called_once_with("/")

    if disable_drive:
        boot_mocks.storage.disable_usb_drive.assert_called_once()
        boot_mocks.usb_cdc.enable.assert_called_once_with(console=True, data=False)
    else:
        boot_mocks.usb_cdc.enable.assert_not_called()
        boot_mocks.storage.disable_usb_drive.assert_not_called()
