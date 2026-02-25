"""Tests for formatting and utility functions."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest


@pytest.mark.parametrize(
    "interval, distance",
    (
        (0, 1),
        (1, 2),
        (5, 3),
        (10, 4),
    )
)
async def test_jiggler(capsys, mouse_mock, async_sleep_mock, interval, distance):
    from src.main import jiggler

    with patch("src.main.jiggle", MagicMock()) as jiggle_mock:
        await jiggler(mouse_mock, interval, distance)

        jiggle_mock.assert_called_once_with(mouse_mock, distance)

        expected_sleeps = [call(1)] * (interval+1)
        async_sleep_mock.assert_has_calls(expected_sleeps)

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
    "command_received, wait_duration, expected_flag_file_content",
    (
        (True, 0.5, "1"),
        (False, 0.05, ""),
    )
)
async def test_serial_command_handling_task(
    capsys, tmpfile, async_sleep_mock, cyp_mocks,
    command_received, wait_duration, expected_flag_file_content
):
    from src.main import serial_command_handling

    handler_mock = AsyncMock()
    handler_mock.command_received = AsyncMock(return_value=command_received)

    await serial_command_handling(handler_mock, tmpfile.__str__())

    stdout, stderr = capsys.readouterr()
    assert not stderr, "Expected no output to stdout"

    if command_received:
        handler_mock.command_received.assert_awaited_once()
        cyp_mocks.microcontroller.reset.assert_called_once()

        assert (
            f"\n!!! Creating temporary flag file {tmpfile.__str__()!r} and rebooting...\n"
            "!!! USB storage will be enabled for next boot only!\n"
        ) == stdout
    else:
        handler_mock.command_received.assert_awaited_once()
        cyp_mocks.microcontroller.assert_not_called()

    async_sleep_mock.assert_awaited_once_with(wait_duration)
    assert tmpfile.read_text() == expected_flag_file_content, "Flag file content mismatch"


async def test_serial_command_handling_task_open_err(capsys):
    from src.main import serial_command_handling

    handler_mock = AsyncMock()
    handler_mock.command_received = AsyncMock(return_value=True)

    some_file = "/some/path"
    excp = OSError("err open")

    with patch("src.main.open", side_effect=excp):
        await serial_command_handling(handler_mock, some_file)

    stdout, stderr = capsys.readouterr()
    assert not stderr, "Expected no output to stdout"
    assert stdout.endswith(f"Could not open/create file {some_file}, error: {excp.__str__()}\n")


async def test_serial_command_handling_task_write_err(capsys):
    from src.main import serial_command_handling

    handler_mock = AsyncMock()
    handler_mock.command_received = AsyncMock(return_value=True)

    some_file = "/some/path"
    excp = OSError("err write")

    file_mock = MagicMock()
    file_mock.write.side_effect = excp

    with patch("src.main.open", return_value=file_mock) as open_mock:
        open_mock.return_value.__enter__.return_value = file_mock
        await serial_command_handling(handler_mock, some_file)

    stdout, stderr = capsys.readouterr()
    assert not stderr, "Expected no output to stdout"
    assert stdout.endswith(f"Could not open/create file {some_file}, error: {excp.__str__()}\n")


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


async def test_main(cyp_mocks, async_sleep_mock):
    cyp_mocks.os.getenv.side_effect = lambda key, default=None: dict(
        enable_drive_flag_file="enable_drive_flag_file",
        enable_drive_button_pin="enable_drive_button_pin",
        button_activation="button_activation",
        tickle_interval="tickle_interval",
        jiggle_distance="jiggle_distance",
        enable_drive_serial_command="enable_drive_serial_command",
    ).get(key, default)

    from src.main import (
        jiggler,
        main,
        serial_command_handling,
        serial_usage_message,
    )

    with (
        patch("src.main.Mouse", MagicMock()) as mouse_mock,
        patch("src.main.setup_usb", MagicMock()) as setup_usb_mock,
        patch("src.main.print_banner", MagicMock()) as print_banner_mock,
        patch("src.main.SerialCommandHandler", MagicMock()) as sch_mock,
        patch("src.main.asyncio.gather", AsyncMock()) as aio_gather_mock,
        patch("src.main.run_forever", MagicMock()) as run_forever_mock,
    ):
        rf_results = [AsyncMock(), AsyncMock(), AsyncMock()]
        run_forever_mock.side_effect = rf_results
        await main()

    mouse_mock.assert_called_once_with(cyp_mocks.usb_hid.devices)
    setup_usb_mock.assert_called_once()
    print_banner_mock.assert_called_once_with("tickle_interval", "jiggle_distance", "enable_drive_serial_command")
    sch_mock.assert_called_once_with("enable_drive_serial_command")

    run_forever_mock.assert_has_calls([
        call(serial_usage_message, "enable_drive_serial_command"),
        call(serial_command_handling, sch_mock.return_value, "enable_drive_flag_file"),
        call(jiggler, mouse_mock.return_value, "tickle_interval", "jiggle_distance")
    ])

    aio_gather_mock.assert_called_once_with(*rf_results)
    async_sleep_mock.assert_has_calls([
        call(5),
    ])
