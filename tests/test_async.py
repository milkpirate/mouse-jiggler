"""Tests for formatting and utility functions."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest


@pytest.mark.parametrize(
    "interval, distance, led",
    (
        (0, 1, None),
        (1, 2, AsyncMock()),
        (5, 3, None),
        (10, 4, AsyncMock())
    )
)
async def test_jiggler(capsys, mouse_mock, async_sleep_mock, interval, distance, led):
    from src.main import jiggler

    with patch("src.main.jiggle", MagicMock()) as jiggle_mock:
        await jiggler(mouse_mock, interval, distance, led)

        jiggle_mock.assert_called_once_with(mouse_mock, distance)

        if led:
            led.fade.assert_has_calls([
                call(to_value=1000, from_value=0, duration=0.5),
                call(to_value=0, from_value=1000, duration=0.5),
            ] * interval)
            led.blink_for.assert_called_once_with(interval=0.25, duration=1)
        else:
            async_sleep_mock.assert_has_calls([call(1)] * (interval+1))

        stdout, stderr = capsys.readouterr()

        expected = " "*50 + "\r"
        expected += '\r'.join([f"Next jiggle in 0min {i}sec... " for i in range(interval, -1, -1)])
        expected += "Jiggle jiggle!\r"

        assert expected == stdout


@pytest.mark.parametrize(
    "enable_cmd",
    (
        "",
        "foo",
        "bar",
    )
)
async def test_serial_usage_message_task(capsys, async_sleep_mock, enable_cmd):
    from src.main import serial_usage_message

    await serial_usage_message(enable_cmd)

    async_sleep_mock.assert_called_once_with(30)
    stdout, stderr = capsys.readouterr()

    assert not stderr, "Expected no output to stdout"
    assert stdout == f"Send: {enable_cmd!r} - to reboot with temporarily enable USB storage\n"


@pytest.mark.parametrize(
    "command_received, wait_duration, exp_nvm",
    (
        (True, 0.5, True),
        (False, 0.05, False),
    )
)
async def test_serial_command_handling_task(
    capsys, tmpfile, async_sleep_mock, cpy_mocks,
    command_received, wait_duration, exp_nvm
):
    cpy_mocks.microcontroller.nvm = bytearray(1)  # ensure nvm is mutable and has at least 1 byte

    from lib.nvm import enable_drive
    from src.main import serial_command_handling

    handler_mock = AsyncMock()
    handler_mock.command_received = AsyncMock(return_value=command_received)

    await serial_command_handling(handler_mock)

    stdout, stderr = capsys.readouterr()
    assert not stderr, "Expected no output to stdout"

    if command_received:
        handler_mock.command_received.assert_awaited_once()
        cpy_mocks.microcontroller.reset.assert_called_once()

        assert (
            "!!! USB storage will be enabled for next boot only !!!\n"
            "Rebooting now...\n"
        ) == stdout
    else:
        handler_mock.command_received.assert_awaited_once()
        cpy_mocks.microcontroller.assert_not_called()

    async_sleep_mock.assert_awaited_once_with(wait_duration)
    assert enable_drive == exp_nvm, "Flag file content mismatch"


async def test_run_forever(async_sleep_mock):
    from src.main import run_forever

    coro_mock = AsyncMock()
    iteration_count = 0

    # make the loop run only 3 iterations by raising CancelledError after 3 calls to sleep
    async def limited_sleep(duration):
        assert duration == 0, "Expected sleep duration to be 0 for run_forever"

        nonlocal iteration_count
        iteration_count += 1
        if iteration_count >= 3:
            raise asyncio.CancelledError()

    async_sleep_mock.side_effect = limited_sleep

    try:
        await run_forever(coro_mock, 123, "abc", foo="bar")
    except asyncio.CancelledError:
        pass

    coro_mock.assert_has_calls(
        [call(123, "abc", foo="bar")]*3
    )


@pytest.mark.parametrize(
    "led_pin, led_inverted",
    (
        (None, False),
        ("LED", True),
    )
)
async def test_setup_led(cpy_mocks, led_pin, led_inverted):
    from src.main import setup_led

    cpy_mocks.board.LED = led_pin
    with (patch("src.main.LED", return_value="some led instance") as led_mock):
        led = setup_led(led_pin, inverted=led_inverted)

        if led_pin:
            assert led == led_mock.return_value
            led_mock.assert_called_once_with(led_pin, inverted=led_inverted, reduce_to=500)
        else:
            assert led is None


@pytest.mark.parametrize("led_pin", (None, "LED"))
@pytest.mark.parametrize("led_active", (0, 1))
async def test_main(cpy_mocks, async_sleep_mock, led_pin, led_active):
    cpy_mocks.os.getenv.side_effect = lambda key, default=None: dict(
        enable_drive_button_pin="enable_drive_button_pin",
        button_activation="button_activation",
        tickle_interval="tickle_interval",
        jiggle_distance="jiggle_distance",
        enable_drive_serial_command="enable_drive_serial_command",
        led_pin=led_pin,
        led_active_low=led_active,
    ).get(key, default)

    from src.main import (
        jiggler,
        main,
        serial_command_handling,
        serial_usage_message,
    )


    if led_pin:
        setup_led_mock = MagicMock(return_value=MagicMock())
        setup_led_mock.return_value.fade = AsyncMock()
    else:
        setup_led_mock = MagicMock(return_value=None)

    with (
        patch("src.main.Mouse", MagicMock()) as mouse_mock,
        patch("src.main.setup_usb", MagicMock()) as setup_usb_mock,
        patch("src.main.print_banner", MagicMock()) as print_banner_mock,
        patch("src.main.SerialCommandHandler", MagicMock()) as sch_mock,
        patch("src.main.asyncio.gather", AsyncMock()) as aio_gather_mock,
        patch("src.main.run_forever", MagicMock()) as run_forever_mock,
        patch("src.main.setup_led", setup_led_mock),
    ):
        rf_results = [AsyncMock(), AsyncMock(), AsyncMock()]
        run_forever_mock.side_effect = rf_results

        await main()

    mouse_mock.assert_called_once_with(cpy_mocks.usb_hid.devices)
    setup_usb_mock.assert_called_once()
    print_banner_mock.assert_called_once_with("tickle_interval", "jiggle_distance", "enable_drive_serial_command")
    sch_mock.assert_called_once_with("enable_drive_serial_command")
    setup_led_mock.assert_called_once_with(led_pin, bool(led_active))

    run_forever_mock.assert_has_calls([
        call(serial_usage_message, "enable_drive_serial_command"),
        call(serial_command_handling, sch_mock.return_value),
        call(jiggler, mouse_mock.return_value, "tickle_interval", "jiggle_distance", setup_led_mock.return_value)
    ])

    aio_gather_mock.assert_called_once_with(*rf_results)

    if led_pin:
        setup_led_mock.return_value.off.assert_called_once()
        setup_led_mock.return_value.fade.assert_called_once_with(to_value=1000, duration=5)
    else:
        async_sleep_mock.assert_called_once_with(5)
