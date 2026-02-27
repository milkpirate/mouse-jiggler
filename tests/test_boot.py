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
def test_is_button_active(cpy_mocks, button_activation, pin_object, button_value, pressed):
    setattr(cpy_mocks.board, "button_name", pin_object)
    cpy_mocks.digitalio.DigitalInOut.return_value.value = button_value

    from boot import is_button_active
    assert is_button_active("button_name", button_activation) == pressed

    if pin_object:
        cpy_mocks.digitalio.DigitalInOut.assert_called_once_with(pin_object)


@pytest.mark.parametrize(
    "enable_drive_by_default", [
        True,   # if drive should be enabled by default, should call enable_drive with False to ensure drive is enabled
        False,  # if drive should not be enabled by default, should not call enable_drive
    ],
)
def test_boot_enable_drive_by_default(
    cpy_mocks, mouse_mock, async_sleep_mock,
    enable_drive_by_default
):
    cpy_mocks.os.remove.side_effect = None
    cpy_mocks.os.getenv.side_effect = lambda key, default=None: dict(
        enable_drive_button_pin="enable_drive_button_pin",
        button_activation="button_activation",
        enable_drive_by_default=int(enable_drive_by_default),
    ).get(key, default)

    from boot import boot

    with (
        patch('boot.is_button_active', return_value=False),
        patch('boot.enable_drive') as enable_drive_mock,
    ):
        boot()

    cpy_mocks.os.getenv.assert_any_call("enable_drive_button_pin")
    cpy_mocks.os.getenv.assert_any_call("button_activation", 0)
    cpy_mocks.os.getenv.assert_any_call("enable_drive_by_default", 0)

    if enable_drive_by_default:
        enable_drive_mock.assert_not_called()
    else:
        enable_drive_mock.assert_called_once_with(int(enable_drive_by_default))


@pytest.mark.parametrize(
    "button_pressed, nvm_enable_drive, must_enable_drive", [
        (False, False, False),  # button not pressed and nvm does not require drive to be enabled, should disable drive
        (False, True, True),    # button not pressed but nvm requires drive to be enabled, should enable drive
        (True, False, True),    # button pressed but nvm does not require drive to be enabled, should enable drive
        (True, True, True),     # button pressed and nvm requires drive to be enabled, should enable drive
    ],
)
def test_boot(
    cpy_mocks, mouse_mock, async_sleep_mock,
    button_pressed, nvm_enable_drive, must_enable_drive
):
    cpy_mocks.os.getenv.side_effect = lambda key, default=None: dict(
        enable_drive_button_pin="enable_drive_button_pin",
        button_activation="button_activation",
        enable_drive_by_default=0,
    ).get(key, default)

    from boot import boot

    with (
        patch('boot.is_button_active', return_value=button_pressed) as is_button_active_mock,
        patch('boot.enable_drive') as enable_drive_mock,
    ):
        enable_drive_mock.__bool__ = MagicMock(return_value=nvm_enable_drive)

        boot()

        is_button_active_mock.assert_called_once_with("enable_drive_button_pin", True)

    cpy_mocks.os.getenv.assert_any_call("enable_drive_button_pin")
    cpy_mocks.os.getenv.assert_any_call("button_activation", 0)
    cpy_mocks.os.getenv.assert_any_call("enable_drive_by_default", 0)

    if must_enable_drive:
        cpy_mocks.storage.disable_usb_drive.assert_not_called()
        cpy_mocks.usb_cdc.enable.assert_not_called()
        enable_drive_mock.assert_called_once_with(False)
    else:
        cpy_mocks.storage.disable_usb_drive.assert_called_once()
        cpy_mocks.usb_cdc.enable.assert_called_once_with(console=True, data=False)
