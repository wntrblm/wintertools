# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""
Just figures out what platform we're on. We currently just use macOS for
factory setup stuff, so this just detects macOS.
"""

import platform


PLATFORM = platform.system()

if PLATFORM == "Darwin":
    MACOS = True
else:
    MACOS = False
