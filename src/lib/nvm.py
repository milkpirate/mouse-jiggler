import microcontroller as mcu


class NVBool:
    def __init__(self, index: int = 0):
        self.index = min(max(0, index), len(mcu.nvm))

    def __bool__(self):
        return bool(mcu.nvm[self.index])

    def __eq__(self, other: bool):
        return self.__bool__() == bool(other)

    def __call__(self, val: bool = None):
        mcu.nvm[self.index] = val
        return self


enable_drive = NVBool(0)
