# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""
Utility for listening for keyboard input in the console.

Only support linux/macos. We don't use windows setup scripts.
"""

import sys

import readchar
import readchar.key

UP = readchar.key.UP
DOWN = readchar.key.DOWN
LEFT = readchar.key.LEFT
RIGHT = readchar.key.RIGHT
ENTER = readchar.key.ENTER


def read():
    key = readchar.readkey()

    if key == readchar.key.CTRL_C:
        raise KeyboardInterrupt()

    if key == readchar.key.CTRL_D:
        sys.exit(1)

    return key


if __name__ == "__main__":
    count = 1
    while True:
        print(count)

        key = read()

        if key == UP:
            count += 1
        elif key == DOWN:
            count -= 1
        elif key == ENTER:
            break

    print("Okey done")
