"""Tests for the host side helper tool (tools/__main__.py)."""
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

# Import the host-side dependencies before the autouse `cpy_mocks` fixture swaps `os`/`time`
# in sys.modules with mocks, otherwise they would be (re-)imported against those mocks.
import docopt  # noqa: F401
import pytest
import serial  # noqa: F401
import serial.tools.list_ports  # noqa: F401
import toml  # noqa: F401

SETTINGS = """
some_string = "foo"
some_int = 42
some_zero = 0
some_empty = ""
some_path = "E:\\\\"
"""


@pytest.fixture
def settings_file(tmpfile, monkeypatch):
    import tools.__main__ as tools_main

    tmpfile.write_text(SETTINGS)
    monkeypatch.setattr(tools_main, "settings_file", tmpfile)
    yield tmpfile


@pytest.mark.parametrize(
    "key, default, expected",
    [
        ("some_string", None, "foo"),
        ("some_int", None, 42),
        ("some_zero", None, 0),       # falsy values are valid settings
        ("some_empty", None, ""),
        ("some_path", None, "E:\\"),
        ("missing", "fallback", "fallback"),
        ("some_string", "fallback", "foo"),     # existing value wins over default
    ],
)
def test_get_setting(settings_file, key, default, expected):
    from tools.__main__ import get_setting

    assert get_setting(key, default) == expected


def test_get_setting_missing(settings_file):
    from tools.__main__ import get_setting

    with pytest.raises(ValueError, match="Setting 'missing' not found in settings.toml"):
        get_setting("missing")


def test_get_setting_real_settings_file():
    from tools.__main__ import get_setting

    assert get_setting("enable_drive_serial_command") == "enable_usb_reboot"


@pytest.mark.parametrize(
    "ports, vid, pid, expected_devices",
    [
        ([], 1, 2, []),
        ([SimpleNamespace(vid=1, pid=2, device="COM1")], 1, 2, ["COM1"]),
        ([SimpleNamespace(vid=1, pid=3, device="COM1")], 1, 2, []),     # pid mismatch
        ([SimpleNamespace(vid=3, pid=2, device="COM1")], 1, 2, []),     # vid mismatch
        (
            [
                SimpleNamespace(vid=1, pid=2, device="COM1"),
                SimpleNamespace(vid=None, pid=None, device="COM2"),     # e.g. non USB port
                SimpleNamespace(vid=1, pid=2, device="COM3"),
            ],
            1, 2, ["COM1", "COM3"],
        ),
    ],
)
def test_find_serial_port(ports, vid, pid, expected_devices):
    from tools.__main__ import find_serial_port

    with patch("tools.__main__.comports", return_value=ports):
        assert [p.device for p in find_serial_port(vid, pid)] == expected_devices


def test_get_cpy_serial_ports():
    from tools.__main__ import get_cpy_serial_ports

    with patch("tools.__main__.find_serial_port", return_value=["port"]) as find_mock:
        assert get_cpy_serial_ports() == ["port"]

    find_mock.assert_called_once_with(vid=0x2e8a, pid=0x103a)


def test_main_setting(capsys):
    from tools.__main__ import main

    with patch("tools.__main__.get_setting", return_value="value") as get_setting_mock:
        main(["setting", "some_key"])

    get_setting_mock.assert_called_once_with("some_key")
    assert capsys.readouterr() == ("value\n", "")


@pytest.mark.parametrize("devices", ([], ["COM1"], ["COM1", "COM7"]))
def test_main_enable_drives(capsys, devices):
    from tools.__main__ import main

    with (
        patch("tools.__main__.get_setting", return_value="cmd") as get_setting_mock,
        patch(
            "tools.__main__.get_cpy_serial_ports",
            return_value=[SimpleNamespace(device=d) for d in devices],
        ),
        patch("tools.__main__.serial.Serial", MagicMock()) as serial_mock,
    ):
        main(["enable_drives"])

    get_setting_mock.assert_called_once_with("enable_drive_serial_command")
    serial_mock.assert_has_calls([call(d, 115200) for d in devices], any_order=True)
    assert serial_mock.call_count == len(devices)

    com = serial_mock.return_value.__enter__.return_value
    com.write.assert_has_calls([call(b"cmd\n")] * len(devices))
    assert com.write.call_count == len(devices)
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize("argv", ([], ["unknown"], ["setting"]))
def test_main_invalid_args(argv):
    from tools.__main__ import main

    with pytest.raises(SystemExit):
        main(argv)
