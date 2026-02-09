import board
import keypad

class SNESCtl:
    buffer = bytearray(2)

    def __init__(self, spi):
        self.spi_device = spi


    @property
    def _raw_inputs(self) -> bytearray:
        with self.spi_device as spi:
            spi.write(b'0x00')
            spi.readinto(self.buffer)
        return self.buffer


snes_ctrl = keypad.ShiftRegisterKeys(
    clock=board.P0_02,
    data=board.P0_04,
    latch=board.P0_06,

    value_to_latch=False,  # CD4021 logic
    key_count=12,  # 12 buttons
    value_when_pressed=False,  # inverse logic

    # interval: float = 0.02
    # , max_events: int = 64,
    # debounce_threshold: int = 1
)


SNES_KEY_NAMES = (
    "B",
    "Y",
    "SELECT",
    "START",
    "UP",
    "DOWN",
    "LEFT",
    "RIGHT",
    "A",
    "X",
    "L",
    "R",
)

