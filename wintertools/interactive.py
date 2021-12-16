# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""Helpers for interactive console programs using the keyboard or gamepad."""

import time

from wintertools import keyboard, tui
from wintertools.gamepad import gamepad


def continue_when_ready():
    if gamepad.connected:
        print(
            tui.bold,
            tui.rgb(255, 190, 240),
            ">> Press A on gamepad when ready.",
            tui.reset,
        )
        while True:
            gamepad.update()
            if gamepad.A.pressed:
                break

    else:
        print(
            tui.bold, tui.rgb(255, 190, 240), ">> Press enter to continue.", tui.reset
        )
        input()


class adjust_value:
    def __init__(self, value, min=None, max=None, interval=1 / 10):
        self.value = value
        self._min = min
        self._max = max
        self._interval = interval

        if gamepad.connected:
            print(
                "Use gamepad to adjust - up/down or left/right to modify, A to accept."
            )
        else:
            print(
                "Use keyboard to adjust - up/down or left/right arrow to change, enter to accept."
            )

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
            if gamepad.connected:
                gamepad.update()

                if time.monotonic() - last_update > self._interval:
                    last_update = time.monotonic()
                    if gamepad.UP or gamepad.RIGHT:
                        self.value = self._clamp(self.value + 1)
                        yield self.value
                    if gamepad.DOWN or gamepad.LEFT:
                        self.value = self._clamp(self.value - 1)
                        yield self.value

                if gamepad.A.pressed:
                    return

                if gamepad.B.pressed:
                    yield self.value

            else:
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
