# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""Helpers for interactive console programs using the keyboard or gamepad."""

import time

from wintertools import keyboard
from wintertools.print import print


def continue_when_ready():
    print("?? Press enter to continue.")
    input()


class adjust_value:
    def __init__(self, value, min=None, max=None, interval=1 / 10):
        self.value = value
        self._min = min
        self._max = max
        self._interval = interval

        print("Use keyboard to adjust - up/down or left/right arrow to change, enter to accept.")

    def _clamp(self, value):
        if self._min:
            value = max(self._min, value)
        if self._max:
            value = min(self._max, value)
        return value

    def __iter__(self):
        last_update = time.monotonic()

        # Yield initial value once.
        yield self.value

        while True:
            key = keyboard.read()
            if key in (keyboard.UP, keyboard.RIGHT):
                self.value = self._clamp(self.value + 1)
                yield self.value
            if key in (keyboard.DOWN, keyboard.LEFT):
                self.value = self._clamp(self.value - 1)
                yield self.value
            if key == keyboard.SPACE:
                yield self.value
            if key == keyboard.ENTER:
                yield self.value
                return
