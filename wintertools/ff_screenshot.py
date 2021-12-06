# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""Helpers for taking screenshots of webpages using Firefox"""

import platform
import subprocess
import sys
import tempfile

if platform.system() == "Darwin":
    _FF_PATH = "/Applications/Firefox.app/Contents/MacOS/firefox"
else:
    _FF_PATH = "firefox"


def capture(url, dst):
    # Use a temporary profile, works around
    with tempfile.TemporaryDirectory() as profile:
        subprocess.run(
            [_FF_PATH, "-headless", "-screenshot", dst, "-profile", profile, url],
            capture_output=False,
        )


if __name__ == "__main__":
    capture(sys.argv[1], sys.argv[2])
