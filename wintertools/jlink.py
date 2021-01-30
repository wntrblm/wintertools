# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""
Helpers for interacting with JLink programmers.
"""

import subprocess

JLINK_PATH = "JLinkExe"


def run(device, script):
    subprocess.check_call(
        [
            JLINK_PATH,
            "-exitonerror",
            "1",
            "-device",
            device,
            "-autoconnect",
            "1",
            "-if",
            "SWD",
            "-speed",
            "4000",
            "-CommanderScript",
            script,
        ]
    )
