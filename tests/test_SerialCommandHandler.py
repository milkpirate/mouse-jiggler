"""Tests for formatting and utility functions."""
from unittest.mock import (
    MagicMock,
    patch,
    AsyncMock,
)


from src.main import (
    SerialCommandHandler
)


def test_SerialCommandHandler_init():
    sch = SerialCommandHandler("cmd")

    assert sch.enable_command == "cmd"
    assert sch.buffer == ""


async def test_SerialCommandHandler_command_received(supervisor_mock):
    sch = SerialCommandHandler("cmd")

    supervisor_mock.runtime.serial_bytes_available = 0
    assert not await sch.command_received()

    bytes_to_read = 4
    supervisor_mock.runtime.serial_bytes_available = bytes_to_read
    with patch("sys.stdin.read", MagicMock(return_value="")) as read_mock:
        assert not await sch.command_received()
        read_mock.assert_called_once_with(bytes_to_read)

    sch.buffer = "preload"
    chunk = "some\rchunk\r\n"
    bytes_to_read = 9
    sch._process_lines = AsyncMock(return_value=False)
    supervisor_mock.runtime.serial_bytes_available = bytes_to_read
    with patch("sys.stdin.read", MagicMock(return_value=chunk[:bytes_to_read])) as read_mock:
        assert not await sch.command_received()
        read_mock.assert_called_once_with(bytes_to_read)
    assert sch.buffer == "preloadsome\nchun"


async def test_SerialCommandHandler__process_lines(capsys, supervisor_mock):
    sch = SerialCommandHandler("cmd")

    sch.buffer = "no LF"
    assert not await sch._process_lines()
    assert capsys.readouterr() == ("", "")

    sch.buffer = "\ntoo early"
    assert not await sch._process_lines()
    assert capsys.readouterr() == ("", "")

    sch.buffer = "cmd\n"
    assert await sch._process_lines()
    assert capsys.readouterr() == ("", "")

    sch.buffer = "no_command\n"
    assert not await sch._process_lines()
    stdout, stderr = capsys.readouterr()
    assert not stderr
    assert stdout == "Unknown command: no_command\nAvailable commands: cmd\n"






