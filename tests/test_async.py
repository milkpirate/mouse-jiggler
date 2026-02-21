"""Tests for formatting and utility functions."""
import asyncio
import pytest

from unittest.mock import MagicMock, call, patch, AsyncMock

from src.main import (
    jiggler,
    serial_usage_message,
    serial_command_handling,
    run_forever,
    main,

    DEFAULT_TICKLE_INTERVAL,
    DEFAULT_JIGGLE_DISTANCE,
)

from src.config import (
    serial_drive_enable_command,
    drive_flag_file,
)


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
    capsys, tmpfile, async_sleep_mock, microcontroller_mock,
    command_received, wait_duration, expected_flag_file_content
):
    handler_mock = AsyncMock()
    handler_mock.command_received = AsyncMock(return_value=command_received)

    await serial_command_handling(handler_mock, tmpfile.__str__())

    stdout, stderr = capsys.readouterr()
    assert not stderr, "Expected no output to stdout"

    if command_received:
        handler_mock.command_received.assert_awaited_once()
        microcontroller_mock.reset.assert_called_once()

        assert (
            f"\n!!! Creating temporary flag file '{tmpfile.__str__()}' and rebooting...\n"
            "!!! USB storage will be enabled for next boot only!\n"
        ) == stdout
    else:
        handler_mock.command_received.assert_awaited_once()
        microcontroller_mock.assert_not_called()

    async_sleep_mock.assert_awaited_once_with(wait_duration)
    assert tmpfile.read_text() == expected_flag_file_content, "Flag file content mismatch"


async def test_serial_command_handling_task_open_err(capsys):
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


async def test_main(usb_hid_mock, async_sleep_mock):
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

    mouse_mock.assert_called_once_with(usb_hid_mock.devices)
    setup_usb_mock.assert_called_once()
    print_banner_mock.assert_called_once_with(
        DEFAULT_TICKLE_INTERVAL, DEFAULT_JIGGLE_DISTANCE, serial_drive_enable_command
    )
    sch_mock.assert_called_once_with(serial_drive_enable_command)

    run_forever_mock.assert_has_calls([
        call(serial_usage_message, serial_drive_enable_command),
        call(serial_command_handling, sch_mock.return_value, drive_flag_file),
        call(jiggler, mouse_mock.return_value, DEFAULT_TICKLE_INTERVAL, DEFAULT_JIGGLE_DISTANCE)
    ])

    aio_gather_mock.assert_called_once_with(*rf_results)
    async_sleep_mock.assert_has_calls([
        call(5),
    ])
