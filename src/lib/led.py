import asyncio

import board
import pwmio


class LED:
    """Class to control an LED connected to a specified pin."""

    _gamma = 2.2
    _hardware_max_duty_cycle = 65535
    _steps = 1000

    def __init__(self, pin: board.Pin, inverted: bool = False, reduce_to: int = _steps):
        self._pwm = pwmio.PWMOut(pin)

        self._inverted = inverted
        self._max_brightness = reduce_to
        self._brightness = 0

        self.off()

    def __del__(self):
        self._pwm.deinit()

    def __enter__(self):
        return self

    def __exit__(self, t, value, traceback):
        self.__del__()

    def _saturate(self, value: int) -> int:
        """Map a value from one range to another, with saturation."""
        return max(0, min(self._max_brightness, value))

    def off(self):
        self.brightness = 0

    def on(self):
        self.brightness = self._steps

    def toggle(self):
        self.brightness = 0 if self.brightness > 0 else self._steps

    async def blink_for(self, interval: float = 0.5, duration: float = 3.0):
        if interval <= 0:
            return
        count = int(duration / interval)
        await self.blink(count, interval / 2)

    async def blink(self, times: int = 3, duration: float = 0.25):
        """Blink the LED a specified number of times."""
        await self.flash(times, duration, duration)

    async def flash(self, times: int = 3, on_duration: float = 0.25, off_duration: float = 0.25):
        """Flash the LED a specified number of times."""
        for _ in range(times):
            self.on()
            await asyncio.sleep(on_duration)
            self.off()
            await asyncio.sleep(off_duration)

    async def fade(self, to_value: int, from_value: int = None, duration: float = 1.0):
        """Fade the LED from current brightness to target brightness over a duration.
        """
        from_value = self._saturate(self.brightness if from_value is None else from_value)
        to_value = self._saturate(to_value)

        if from_value == to_value:
            self.brightness = to_value
            await asyncio.sleep(duration)
            return

        steps = abs(to_value - from_value)
        step_duration = duration / steps
        brightness_step = 1 if to_value > from_value else -1

        for i in range(steps + 1):
            self.brightness = from_value + (brightness_step * i)
            await asyncio.sleep(step_duration)

    @property
    def brightness(self):
        """Get the current LED brightness."""
        return self._brightness

    @brightness.setter
    def brightness(self, brightness: int):
        """Set the LED brightness (0 to 100.0) with gamma correction."""

        brightness = self._saturate(brightness)
        self._brightness = brightness

        normalized = (brightness / self._steps) ** self._gamma
        duty_cycle = int(normalized * self._hardware_max_duty_cycle)

        if self._inverted:
            duty_cycle = self._hardware_max_duty_cycle - duty_cycle

        self._pwm.duty_cycle = duty_cycle
