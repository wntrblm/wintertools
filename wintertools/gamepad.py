# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""A simple interface to Gamepads used by us during setup."""

import atexit

import hid


class _ButtonMask:
    UP = (4, 0)
    DOWN = (4, 255)
    LEFT = (3, 0)
    RIGHT = (3, 255)
    A = (0, 4)
    B = (0, 2)
    C = (0, 128)
    X = (0, 8)
    Y = (0, 1)
    Z = (0, 64)
    L = (0, 16)
    R = (0, 32)
    START = (1, 2)


class Button:
    def __init__(self):
        self._value = False
        self._last_value = False
        pass

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._last_value = self._value
        self._value = value

    @property
    def pressed(self):
        return self._last_value is False and self._value is True

    @property
    def released(self):
        return self._last_value is False and self._value is True

    def __str__(self):
        return f"{self.value}"

    def __bool__(self):
        return self.value


class Gamepad:
    # Saturn Gamepad
    VENDOR_ID = 3853
    PRODUCT_ID = 193

    def __init__(self):
        self._last_report = None

        try:
            self._device = hid.device()
            self._device.open(self.VENDOR_ID, self.PRODUCT_ID)
            self._device.set_nonblocking(True)
        except IOError:
            self._device = None

        self.UP = Button()
        self.DOWN = Button()
        self.LEFT = Button()
        self.RIGHT = Button()
        self.A = Button()
        self.B = Button()
        self.C = Button()
        self.X = Button()
        self.Y = Button()
        self.Z = Button()
        self.L = Button()
        self.R = Button()
        self.START = Button()

    def __del__(self):
        self.close()

    def close(self):
        if self.connected:
            self._device.close()
            self._device = None

    @property
    def connected(self):
        return self._device is not None

    def update(self):
        if self._device is None:
            return False

        report = None
        while not report:
            report = self._device.read(64)
            pass

        self.UP = report[_ButtonMask.UP[0]] == _ButtonMask.UP[1]
        self.DOWN = report[_ButtonMask.DOWN[0]] == _ButtonMask.DOWN[1]
        self.LEFT = report[_ButtonMask.LEFT[0]] == _ButtonMask.LEFT[1]
        self.RIGHT = report[_ButtonMask.RIGHT[0]] == _ButtonMask.RIGHT[1]
        self.A.value = bool(report[_ButtonMask.A[0]] & _ButtonMask.A[1])
        self.B.value = bool(report[_ButtonMask.B[0]] & _ButtonMask.B[1])
        self.C.value = bool(report[_ButtonMask.C[0]] & _ButtonMask.C[1])
        self.X.value = bool(report[_ButtonMask.X[0]] & _ButtonMask.X[1])
        self.Y.value = bool(report[_ButtonMask.Y[0]] & _ButtonMask.Y[1])
        self.Z.value = bool(report[_ButtonMask.Z[0]] & _ButtonMask.Z[1])
        self.L.value = bool(report[_ButtonMask.L[0]] & _ButtonMask.L[1])
        self.R.value = bool(report[_ButtonMask.R[0]] & _ButtonMask.R[1])
        self.START.value = bool(report[_ButtonMask.START[0]] & _ButtonMask.START[1])

        self._last_report = report

        return True

    def __str__(self):
        return f"<Gamepad up: {self.UP}, down: {self.DOWN}, left: {self.LEFT}, right: {self.RIGHT}, a: {self.A} b: {self.B} c: {self.C} x: {self.X} y: {self.Y}  z: {self.Z} l: {self.L} r: {self.R} start: {self.START}>"


gamepad = Gamepad()

atexit.register(lambda: gamepad.close())
