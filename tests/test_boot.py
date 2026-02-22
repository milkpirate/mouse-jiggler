from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.parametrize(
    "button_activation, pin_object, button_value, pressed", [
        (False, None, True, False),     # button activation is active low but pin object does not exist, should
                                        # return False
        (True, None, False, False),     # button activation is active high but pin object does not exist, should
                                        # return False
        (False, MagicMock(), True, False),  # button activation is active low and pin object exists but button not
                                            # pressed, should return False
        (False, MagicMock(), False, True),  # button activation is active low and pin object exists and button pressed,
                                            # should return True
        (True, MagicMock(), True, True),    # button activation is active high and pin object exists and button pressed,
                                            # should return True
        (True, MagicMock(), False, False),  # button activation is active high and pin object exists but button not
                                            # pressed, should return False
    ],
)
def test_is_button_active(circuit_python_mocks, button_activation, pin_object, button_value, pressed):
    setattr(circuit_python_mocks.board, "button_name", pin_object)
    circuit_python_mocks.digitalio.DigitalInOut.return_value.value = button_value

    from boot import is_button_active
    assert is_button_active("button_name", button_activation) == pressed

    if pin_object:
        circuit_python_mocks.digitalio.DigitalInOut.assert_called_once_with(pin_object)


@pytest.mark.parametrize(
    "drive_flag_file, files, list_error, exists", [
        (None, [], None, False),  # no drive flag file specified
        ("flag.txt", ["foo", "flag.txt"], None, True),  # drive flag file exists
        ("flag.txt", ["foo", "bar"], None, False),  # drive flag file does not exist
        ("flag.txt", [], OSError("list err"), False),  # listdir raises an error
        (None, [], OSError("list err"), False),  # no drive flag file specified and listdir raises an error
    ],
)
def test_file_exists(circuit_python_mocks, drive_flag_file, files, list_error, exists):
    circuit_python_mocks.os.listdir.return_value = files
    circuit_python_mocks.os.listdir.side_effect = list_error

    from boot import file_exists
    assert file_exists(drive_flag_file) == exists


@pytest.mark.parametrize(
    "button_pressed, file_exists, rm_error, enable_drive", [
        (False, False, None, False),  # button not pressed and file does not exist, should disable drive
        (True, False, None, True),  # button pressed and file does not exist, should enable drive
        (False, True, None, True),  # button not pressed but file exists, should enable drive
        (True, True, None, True),  # button pressed and file exists, should
        (False, False, OSError("rm err"), False),   # button not pressed and file does not exist but remove raises
                                                    # an error, should disable drive
        (False, True, OSError("rm err"), True),     # button not pressed but file exists and remove raises an error,
                                                    # should enable drive
        (True, False, OSError("rm err"), True),     # button pressed and file does not exist but remove raises an
                                                    # error, should enable drive
        (True, True, OSError("rm err"), True),      # button pressed and file exists but remove raises an error,
                                                    # should enable drive
    ],
)
def test_boot(circuit_python_mocks, mouse_mock, async_sleep_mock, button_pressed, file_exists, rm_error, enable_drive):
    circuit_python_mocks.os.remove.side_effect = rm_error
    circuit_python_mocks.os.getenv.side_effect = lambda key, default=None: dict(
        drive_flag_file="drive_flag_file",
        button_pin="button_pin",
        button_activation="button_activation",
    ).get(key, default)

    from boot import boot

    with (
        patch('boot.is_button_active', return_value=button_pressed) as is_button_active_mock,
        patch('boot.file_exists', return_value=file_exists) as file_exists_mock,
    ):
        boot()

        is_button_active_mock.assert_called_once_with("button_pin", True)
        file_exists_mock.assert_called_once_with("drive_flag_file")

    circuit_python_mocks.os.getenv.assert_any_call("drive_flag_file")
    circuit_python_mocks.os.getenv.assert_any_call("button_pin")
    circuit_python_mocks.os.getenv.assert_any_call("button_activation", 0)

    if file_exists:
        circuit_python_mocks.os.remove.assert_called_once_with("drive_flag_file")

    if enable_drive:
        circuit_python_mocks.storage.disable_usb_drive.assert_not_called()
        circuit_python_mocks.usb_cdc.enable.assert_not_called()
    else:
        circuit_python_mocks.storage.disable_usb_drive.assert_called_once()
        circuit_python_mocks.usb_cdc.enable.assert_called_once_with(console=True, data=False)
