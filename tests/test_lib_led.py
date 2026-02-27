"""Tests for formatting and utility functions."""
from unittest.mock import AsyncMock, MagicMock, PropertyMock, call, patch

import pytest


@pytest.mark.parametrize(
    "pin, inverted, reduce_to",
    [
        ("pin1", False, 255),
        ("pin2", True, 128),
        ("pin3", False, 0),
        ("pin4", True, 10000),
    ],
)
def test_led__init__(cpy_mocks, pin, inverted, reduce_to):
    from src.lib.led import LED

    pin = cpy_mocks.board.Pin(pin)
    LED.off = MagicMock()

    led = LED(pin, inverted, reduce_to)

    assert led._pwm is not None
    assert led._inverted == inverted
    assert led._max_brightness == reduce_to
    assert led._brightness == 0

    LED.off.assert_called_once()
    cpy_mocks.pwmio.PWMOut.assert_called_once_with(pin)


def test_led__init__defaults(cpy_mocks):
    from src.lib.led import LED

    pin = cpy_mocks.board.Pin('pin')
    led = LED(pin)

    assert not led._inverted
    assert led._max_brightness == LED._steps


def test_led__del__(cpy_mocks):
    from src.lib.led import LED

    led = LED(cpy_mocks.board.Pin('pin'))
    led.__del__()

    led._pwm.deinit.assert_called_once()


def test_led__exit__(cpy_mocks):
    from src.lib.led import LED

    led = LED(cpy_mocks.board.Pin('pin'))
    led.__exit__(None, None, None)

    led._pwm.deinit.assert_called_once()


def test_led__enter__(cpy_mocks):
    from src.lib.led import LED

    led = LED(cpy_mocks.board.Pin('pin'))
    enter = led.__enter__()

    assert led == enter


@pytest.mark.parametrize(
    "method, brightness_value",
    [
        ("off", 0),
        ("on", None),   # None means it should use led._steps as the brightness value
    ]
)
def test_led_on(cpy_mocks, method, brightness_value):
    from src.lib.led import LED

    pin = cpy_mocks.board.Pin('pin')

    with patch.object(LED, "brightness", new_callable=PropertyMock) as mock_brightness:
        led = LED(pin)
        getattr(led, method)()
        mock_brightness.assert_has_calls([
            call(0),
            call(brightness_value if brightness_value is not None else led._steps),
        ])


def test_led_toggle(cpy_mocks):
    from src.lib.led import LED

    led = LED(cpy_mocks.board.Pin('pin'))

    led.brightness = 0
    led.toggle()
    assert led.brightness == led._steps

    led.toggle()
    assert led.brightness == 0


async def test_blink_for_default(cpy_mocks):
    from src.lib.led import LED

    led = LED(cpy_mocks.board.Pin('pin'))
    led.blink = AsyncMock()

    await led.blink_for()
    led.blink.assert_called_once_with(6, 0.25)


@pytest.mark.parametrize(
    "interval, duration, expected_times, expected_duration",
    [
        (0.5, 3.0, 6, 0.25),
        (1.0, 5.0, 5, 0.5),
        (0.25, 2.0, 8, 0.125),
        (0.1, 1.0, 10, 0.05),
        (0.2, 4.0, 20, 0.1),
        (-1, None, None, None),
    ]
)
async def test_blink_for(cpy_mocks, interval, duration, expected_times, expected_duration):
    from src.lib.led import LED

    led = LED(cpy_mocks.board.Pin('pin'))
    led.blink = AsyncMock()

    await led.blink_for(interval, duration)

    if interval <= 0:
        led.blink.assert_not_called()
    else:
        led.blink.assert_called_once_with(expected_times, expected_duration)


async def test_blink_default(cpy_mocks):
    from src.lib.led import LED

    led = LED(cpy_mocks.board.Pin('pin'))
    led.flash = AsyncMock()

    await led.blink()

    led.flash.assert_called_once_with(3, 0.25, 0.25)


@pytest.mark.parametrize(
    "times, duration",
    [
        (5, 0.5),
        (2, 1.0),
        (10, 0.25),
        (3, 0.75),
    ]
)
async def test_blink(cpy_mocks, times, duration):
    from src.lib.led import LED

    led = LED(cpy_mocks.board.Pin('pin'))
    led.flash = AsyncMock()

    await led.blink(times, duration)

    led.flash.assert_called_once_with(times, duration, duration)


async def test_flash_default(cpy_mocks, async_sleep_mock):
    from src.lib.led import LED

    led = LED(cpy_mocks.board.Pin('pin'))
    led.on = MagicMock()
    led.off = MagicMock()

    await led.flash()

    led.on.assert_has_calls([call()]*3)
    led.off.assert_has_calls([call()]*3)
    async_sleep_mock.assert_has_calls([call(0.25)]*3*2)


@pytest.mark.parametrize(
    "brightness, to_value, from_value, duration, brightnesses, step_durations",
    [
        # fade to max brightness from current brightness
        (123, 255, None, 1.0, range(123, 256), 0.007575757575757576),
        # fade to mid-brightness from off
        (0, 128, None, 2.0, range(0, 129), 0.015625),
        # fade to off from max brightness
        (255, 0, None, 1.0, range(255, -1, -1), 0.00392156862745098),
        # fade to high brightness from mid-brightness
        (50, 200, 100, 1.5, range(100, 201), 0.015),
        # fade to low brightness from mid-brightness
        (200, 50, 150, 2.0, range(150, 49, -1), 0.02),
        # fade to same brightness should just set brightness and sleep for duration
        (100, 100, None, 1.0, [100], 1.0),
        # fade to same brightness from different from_value should just set brightness and sleep for duration
        (100, 100, 150, 1.0, [150], 1.0),
        # fade to higher brightness from lower brightness
        (100, 150, 50, 1.0, range(50, 151), 0.01),
        # fade to lower brightness from higher brightness
        (150, 50, 60, 1.0, range(60, 49, -1), 0.1),
    ],
)
async def test_fade(
    cpy_mocks, async_sleep_mock,
    brightness, to_value, from_value, duration, brightnesses, step_durations
):
    from src.lib.led import LED

    with patch.object(LED, "brightness", new_callable=PropertyMock) as mock_brightness:
        mock_brightness.return_value = brightness
        led = LED(cpy_mocks.board.Pin('pin'))
        await led.fade(to_value, from_value, duration)

        async_sleep_mock.assert_has_calls(
            [call(step_durations)] * (len(brightnesses) - 1)
        )
        mock_brightness.assert_has_calls(
            [call(b) for b in brightnesses]
        )


def test_brightness_getter(cpy_mocks):
    from src.lib.led import LED

    led = LED(cpy_mocks.board.Pin('pin'))
    led._brightness = 123

    assert led.brightness == 123


@pytest.mark.parametrize(
    "set_brightness, exp_brightness, exp_duty_cycle, inverted",
    [
        (50, 50, 89, False),
        (100, 100, 413, False),
        (-10, 0, 0, False),
        (500, 500, 14262, False),
        (0, 0, 65535, True),
        (128, 128, 64824, True),
        (2000, 1000, 0, True),
        (500, 500, 51273, True),
        (-50, 0, 65535, True),
    ]
)
def test_brightness_setter(cpy_mocks, set_brightness, exp_brightness, exp_duty_cycle, inverted):
    from src.lib.led import LED
    led = LED(cpy_mocks.board.Pin('pin'), inverted=inverted)

    led.brightness = set_brightness

    assert led._brightness == exp_brightness
    assert led._pwm.duty_cycle == exp_duty_cycle
