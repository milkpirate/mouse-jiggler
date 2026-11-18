"""Tests for the POSIX-like helper functions."""
from unittest.mock import call, patch

import pytest

DIR_MODE = 0b0100_0000_0000_0000 | 0o755
FILE_MODE = 0b1000_0000_0000_0000 | 0o644


def _stat(mode: int, size: int = 0, mtime: int = 0) -> tuple:
    """Build an os.stat() like tuple: (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime)."""
    return mode, 0, 0, 0, 0, 0, size, 0, mtime, 0


@pytest.mark.parametrize(
    "s, width, expected",
    [
        ("a", 3, "  a"),
        ("abc", 3, "abc"),      # exact width, no padding
        ("abcd", 2, "abcd"),    # longer than width, no truncation
        ("", 2, "  "),
        ("x", 0, "x"),
        ("x", -1, "x"),
    ],
)
def test__rjust(cpy_mocks, s, width, expected):
    from src.lib.posiks import _rjust

    assert _rjust(s, width) == expected


@pytest.mark.parametrize(
    "size, expected",
    [
        (0, "    0"),
        (1, "    1"),
        (1023, " 1023"),
        (1024, "1.0KB"),
        (1536, "1.5KB"),
        (2048, "2.0KB"),
        (10 * 1024, "10.0KB"),  # wider than 5, no truncation
        (1024 ** 2, "1.0MB"),
        (1024 ** 3, "1.0GB"),
        (1024 ** 4, "1.0TB"),
        (2 * 1024 ** 4, "2.0TB"),
    ],
)
def test__format_size(cpy_mocks, size, expected):
    from src.lib.posiks import _format_size

    assert _format_size(size) == expected


@pytest.mark.parametrize(
    "mode, is_dir",
    [
        (DIR_MODE, True),
        (FILE_MODE, False),
        (0, False),
    ],
)
def test__is_dir(cpy_mocks, mode, is_dir):
    cpy_mocks.os.stat.return_value = _stat(mode)

    from src.lib.posiks import _is_dir

    assert _is_dir("some/path") == is_dir
    cpy_mocks.os.stat.assert_called_once_with("some/path")


@pytest.mark.parametrize("path", (None, ".", "/lib", "/lib/", "/"))
def test_ls(capsys, cpy_mocks, path):
    exp_path = path or "."
    prefix = exp_path.rstrip("/")
    stats = {
        f"{prefix}/b.txt": _stat(FILE_MODE, size=10),
        f"{prefix}/adir": _stat(DIR_MODE),
        f"{prefix}/a.txt": _stat(FILE_MODE, size=2048),
    }
    listing = ["b.txt", "adir", "a.txt"]

    cpy_mocks.os.sep = "/"
    cpy_mocks.os.listdir.return_value = listing
    cpy_mocks.os.stat.side_effect = lambda p: stats[p]
    cpy_mocks.time.localtime.return_value = (2024, 1, 2, 3, 4, 5, 0, 0, 0)

    from src.lib.posiks import ls

    result = ls() if path is None else ls(path)

    assert result == listing, "Expected the unsorted raw listing to be returned"
    cpy_mocks.os.listdir.assert_called_once_with(exp_path)

    stdout, stderr = capsys.readouterr()
    assert not stderr
    assert stdout == (
        "    0 2024-01-02 03:04 adir/\n"     # directories first
        "2.0KB 2024-01-02 03:04 a.txt\n"
        "   10 2024-01-02 03:04 b.txt\n"
    )


def test_ls_empty(capsys, cpy_mocks):
    cpy_mocks.os.listdir.return_value = []

    from src.lib.posiks import ls

    assert ls() == []
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize("content", ("", "hello", "hello\nworld\n"))
def test_cat(capsys, cpy_mocks, tmpfile, content):
    tmpfile.write_text(content)

    from src.lib.posiks import cat

    assert cat(str(tmpfile)) == content
    assert capsys.readouterr() == (content + "\n", "")


@pytest.mark.parametrize(
    "func, mode, os_func, stdout",
    [
        ("rm", FILE_MODE, "remove", ""),
        ("rm", DIR_MODE, None, "Error: 'some/path' is a directory. Use rmdir to remove directories.\n"),
        ("rmdir", DIR_MODE, "rmdir", ""),
        ("rmdir", FILE_MODE, None, "Error: 'some/path' is not a directory. Use rm to remove files.\n"),
    ],
)
def test_rm_rmdir(capsys, cpy_mocks, func, mode, os_func, stdout):
    cpy_mocks.os.stat.return_value = _stat(mode)

    from src.lib import posiks

    getattr(posiks, func)("some/path")

    for name in ("remove", "rmdir"):
        if name == os_func:
            getattr(cpy_mocks.os, name).assert_called_once_with("some/path")
        else:
            getattr(cpy_mocks.os, name).assert_not_called()

    assert capsys.readouterr() == (stdout, "")


def test_touch_creates_file(cpy_mocks, tmp_path):
    from src.lib.posiks import touch

    path = tmp_path / "new_file"
    touch(str(path))

    assert path.exists()
    assert path.read_text() == ""


def test_touch_keeps_content(cpy_mocks, tmpfile):
    tmpfile.write_text("keep me")

    from src.lib.posiks import touch

    touch(str(tmpfile))

    assert tmpfile.read_text() == "keep me"


def test_reboot(cpy_mocks):
    from src.lib.posiks import reboot

    reboot()

    cpy_mocks.microcontroller.reset.assert_called_once_with()


def test_uname(capsys, cpy_mocks):
    uname = ("rp2040", "rp2040", "10.0.3", "10.0.3 on 2025-01-01", "Waveshare RP2040-One with rp2040")
    cpy_mocks.os.uname.return_value = uname

    from src.lib.posiks import uname as posiks_uname

    assert posiks_uname() == uname
    assert capsys.readouterr() == (" ".join(uname) + "\n", "")


def test_pwd(capsys, cpy_mocks):
    cpy_mocks.os.getcwd.return_value = "/lib"

    from src.lib.posiks import pwd

    assert pwd() == "/lib"
    assert capsys.readouterr() == ("/lib\n", "")


def test_env(cpy_mocks):
    from src.lib.posiks import env

    with patch("src.lib.posiks.cat", return_value="settings content") as cat_mock:
        assert env() == "settings content"

    cat_mock.assert_called_once_with("/settings.toml")


@pytest.mark.parametrize(
    "func, storage_call",
    [
        ("fmt", call.erase_filesystem()),
        ("rwmount", call.remount("/", readonly=False)),
    ],
)
def test_storage_helpers(cpy_mocks, func, storage_call):
    from src.lib import posiks

    getattr(posiks, func)()

    assert cpy_mocks.storage.mock_calls == [storage_call]
