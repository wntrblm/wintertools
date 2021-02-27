# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""Thin wrappers over subprocess"""

import subprocess

from wintertools import log


def run(*args, capture=True):
    log.debug("$ " + " ".join(args))
    return subprocess.run(
        args, capture_output=capture, encoding="utf-8", check=True
    ).stdout
