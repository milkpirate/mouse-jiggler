"""Tests for formatting and utility functions."""
from unittest.mock import call

import pytest


@pytest.mark.parametrize(
    "duration, expected",
    [
        (-123, "0min 0sec"),  # Negative duration should be treated as zero
        (0, "0min 0sec"),
        (30, "0min 30sec"),
        (59, "0min 59sec"),
        (60, "1min 0sec"),
        (120, "2min 0sec"),
        (90, "1min 30sec"),
        (125, "2min 5sec"),
        (300, "5min 0sec"),
        (5 * 60, "5min 0sec"),
        (3661, "61min 1sec"),
        (65.5, "1min 5sec"),
        (90.9, "1min 30sec"),
    ],
)
def test_min_sec_fmt(duration, expected):
    from src.main import min_sec_fmt

    assert min_sec_fmt(duration) == expected


@pytest.mark.parametrize(
    "distance",
    [-3, 4, 0, 1, 10],
)
def test_jiggle(mouse_mock, distance):
    from src.main import jiggle

    jiggle(mouse_mock, distance)

    mouse_mock.move.assert_has_calls([
        call(x=distance),
        call(x=-distance),
    ], any_order=False)


def test_setup_usb(cpy_mocks):
    from src.main import setup_usb

    setup_usb()

    cpy_mocks.supervisor.set_usb_identification.assert_called_once_with("CPY", "Mouse MJ2040")
    cpy_mocks.usb_hid.set_interface_name.assert_called_once_with("CPY Mouse MJ2040")


def test_print_banner(capsys):
    from src.main import print_banner

    interval = 123
    distance = 234
    enable_cmd = "enable_cmd"

    print_banner(interval, distance, enable_cmd)

    stdout, stderr = capsys.readouterr()

    assert not stderr, "Expected no output to stdout"
    assert (
        f"Mouse jiggler started!\n\n"
        f"Interval {interval//60}min {interval%60}sec\n"
        f"Distance \xb1{distance}px\n"
        f"Serial command: '{enable_cmd}' - to reboot with temporarily enable USB storage\n"
        f"Enter main loop...\n\n"
    ) == stdout
