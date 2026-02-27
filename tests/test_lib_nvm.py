"""Tests for formatting and utility functions."""
import pytest


@pytest.mark.parametrize(
    "idx, set_idx",[
        (0, 0),
        (-1, 0),
        (20, 16),
    ]
)
def test_nvm__init__(cpy_mocks, idx, set_idx):
    from lib.nvm import NVBool
    b = NVBool(idx)
    assert b.index == set_idx


def test_nvm__init__default(cpy_mocks):
    from lib.nvm import NVBool
    assert NVBool().index == 0


def test_nvm__bool__(cpy_mocks):
    cpy_mocks.microcontroller.nvm = bytearray(b"\xaa\x55\xff\x00")

    from lib.nvm import NVBool
    assert NVBool(0) == True  # noqa: E712
    assert NVBool(1) == True  # noqa: E712
    assert NVBool(2) == True  # noqa: E712
    assert NVBool(3) == False  # noqa: E712


def test_nvm__call__(cpy_mocks):
    cpy_mocks.microcontroller.nvm = bytearray(b"\xaa\x55\xff\x00")

    from lib.nvm import NVBool

    b = NVBool(1)
    b(False)
    assert b == False  # noqa: E712

    b = NVBool(3)
    b(True)
    assert b == True  # noqa: E712
