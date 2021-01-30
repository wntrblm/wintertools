# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""
Replaces input with a very noisy variant. ;)
"""

import subprocess

import wintertools.platform


def bell():
    if wintertools.platform.MACOS:
        subprocess.call(["say", "Ding!"])
    else:
        print("\a")


_original_input = __builtins__["input"]


def input_with_bell(*args, **kwargs):
    bell()
    return _original_input(*args, **kwargs)


__builtins__["input"] = input_with_bell
