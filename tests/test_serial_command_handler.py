from unittest.mock import MagicMock, patch

import pytest


def test_SerialCommandHandler_init():  # noqa: N802
    from src.main import SerialCommandHandler

    sch = SerialCommandHandler("cmd")

    assert sch.enable_command == "cmd"
    assert sch.buffer == b""


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
def test_SerialCommandHandler__fill_reader(cyp_mocks, available_bytes, read_data, expected_result):  # noqa: N802
    from src.main import SerialCommandHandler
    sch = SerialCommandHandler("cmd")

    with patch("main.sys.stdin.read") as stdin_read_mock:
        cyp_mocks.supervisor.runtime.serial_bytes_available = available_bytes
        stdin_read_mock.return_value = read_data

        assert sch._fill_buffer() == expected_result

        if available_bytes:
            stdin_read_mock.assert_called_once_with(available_bytes)
        else:
            stdin_read_mock.assert_not_called()


@pytest.mark.parametrize(
    "stdin, stdout, read_out, buffer", [
        (None, "", None, None),
        (None, "Error reading from serial: read error\n", None, None),
        ("line_data".encode(), "", None, "line_data".encode()),
        (
            "line_data\nsome other line\n\nand even more".encode(),
            "",
            "line_data",
            "some other line\n\nand even more".encode()
        ),
    ]
)
def test_SerialCommandHandler__extract_first_complete_line(    # noqa: N802
    capsys, cyp_mocks,
    stdin, stdout, read_out, buffer
):
    from src.main import SerialCommandHandler

    sch = SerialCommandHandler("cmd")
    sch.buffer = stdin

    assert sch._extract_first_complete_line() == read_out
    assert sch.buffer == buffer


@pytest.mark.parametrize(
    "_fill_buffer, line, stdout, command_received", [
        (False, None, "", False),   # _fill_buffer returning False should short circuit and return False without
                                    # calling _read_out
        (True, None, "", False),    # _fill_buffer returning True but no complete line is None, should return False
        (True, "not_cmd", "Unknown command: 'not_cmd'\nAvailable commands: 'cmd'\n", False),
                                    # unrecognized command should print error and return False
        (True, "cmd", "", True),    # recognized command should return True
    ]
)
async def test_SerialCommandHandler_command_received(  # noqa: N802
    capsys, cyp_mocks,
    _fill_buffer, line, stdout, command_received
):
    from src.main import SerialCommandHandler

    sch = SerialCommandHandler("cmd")
    sch.buffer = line
    sch._fill_buffer = MagicMock(return_value=_fill_buffer)
    sch._extract_first_complete_line = MagicMock(return_value=line)

    assert await sch.command_received() == command_received
    assert capsys.readouterr() == (stdout, "")
