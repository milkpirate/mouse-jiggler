import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def test_SerialCommandHandler_init():  # noqa: N802
    from src.main import SerialCommandHandler

    with patch("main.asyncio.StreamReader") as reader_mock:
        sch = SerialCommandHandler("cmd")

    assert sch.enable_command == "cmd"
    assert sch.reader == reader_mock()


@pytest.mark.parametrize(
    "available_bytes, read_data, expected_result", [
        (0, None, False),
        (4, "", False),
        (4, "data", True),
        (4, b"data", True),
        (4, "data\nmore_data", True),
        (4, "data\n", True),
        (4, "\n", True),
        (4, "\n\n", True),
    ]
)
def test_SerialCommandHandler__fill_reader(circuit_python_mocks, available_bytes, read_data, expected_result):  # noqa: N802
    from src.main import SerialCommandHandler

    with (
        patch("main.sys.stdin.read") as stdin_read_mock,
        patch("main.asyncio.StreamReader") as stream_reader_mock,
    ):
        sch = SerialCommandHandler("cmd")
        sch.reader = stream_reader_mock

        circuit_python_mocks.supervisor.runtime.serial_bytes_available = available_bytes
        stdin_read_mock.return_value = read_data

        assert sch._fill_reader() == expected_result

        if available_bytes:
            stdin_read_mock.assert_called_once_with(available_bytes)
            if read_data:
                expected_chunk = read_data.encode() if isinstance(read_data, str) else read_data
                stream_reader_mock.feed_data.assert_called_once_with(expected_chunk)
        else:
            stdin_read_mock.assert_not_called()


@pytest.mark.parametrize(
    "wait_for_return, wait_for_exception, stdout, readline, read_out", [
        (None, asyncio.TimeoutError, "", None, None),
        (None, Exception("read error"), "Error reading from serial: read error\n", None, None),
        ("  line_data\n".encode(), None, "", "line_data\n".encode(), "line_data"),
    ]
)
async def test_SerialCommandHandler__read_out(    # noqa: N802
    capsys, circuit_python_mocks,
    wait_for_return, wait_for_exception, stdout, readline, read_out
):
    from src.main import SerialCommandHandler

    with (
        patch("main.asyncio.wait_for", AsyncMock(
            return_value=wait_for_return,
            side_effect=wait_for_exception,
        )) as wait_for_mock
    ):
        sch = SerialCommandHandler("cmd")

        sch.reader = MagicMock()
        sch.reader.readline.return_value = readline

        result = await sch._read_out()

        assert result == read_out
        assert capsys.readouterr() == (stdout, "")
        wait_for_mock.assert_called_once_with(sch.reader.readline.return_value, timeout=0.01)


@pytest.mark.parametrize(
    "fill_reader, read_out, stdout, command_received", [
        (False, None, "", False),   # fill_reader returning False should short circuit and return False without
                                    # calling _read_out
        (True, None, "", False),    # _read_out returning None should short circuit and return False
        (True, "not_cmd", "Unknown command: 'not_cmd'\nAvailable commands: cmd\n", False),
                                    # unrecognized command should print error and return False
        (True, "cmd", "", True),    # recognized command should return True
    ]
)
async def test_SerialCommandHandler_command_received(  # noqa: N802
    capsys, circuit_python_mocks,
    fill_reader, read_out, stdout, command_received
):
    from src.main import SerialCommandHandler

    sch = SerialCommandHandler("cmd")
    sch._fill_reader = MagicMock(return_value=fill_reader)
    sch._read_out = AsyncMock(return_value=read_out)

    assert await sch.command_received() == command_received
    assert capsys.readouterr() == (stdout, "")
