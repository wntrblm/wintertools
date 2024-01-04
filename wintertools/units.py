# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""
Helpers for formatting units
"""

import math


def _format_unit(
    value, *, formats, use_fullname=False, use_space=True, precision=2
) -> str:
    space = " " if use_space else ""
    name = ""

    for [max, mult, fullname, shortname] in formats:
        if abs(value) < max:
            value *= mult
            name = fullname if use_fullname else shortname
            break

    return f"{value:.{precision}f}{space}{name}"


_SECONDS_FORMATS = [
    [0.0000001, 1000000000, "nanoseconds", "ns"],
    [0.001, 1000000, "microseconds", "μs"],
    [1, 1000, "milliseconds", "ms"],
    [3600, 1, "seconds", "s"],
    [math.inf, 1 / 60, "hours", "h"],
]


def format_seconds(seconds, **kwargs):
    return _format_unit(seconds, formats=_SECONDS_FORMATS, **kwargs)


_HERTZ_FORMATS = [
    [0.0000001, 1000000000, "nanohertz", "nHz"],
    [0.001, 1000000, "microhertz", "μHz"],
    [1, 1000, "millihertz", "mHz"],
    [1000, 1, "hertz", "Hz"],
    [1000000, 1 / 1000, "kilohertz", "kHz"],
    [1000000000, 1 / 1000000, "megahertz", "Hz"],
    [1000000000000, 1 / 1000000000, "gigahertz", "GHz"],
    [math.inf, 1 / 1000000000000, "terahertz", "THz"],
]


def format_hertz(hertz, **kwargs):
    return _format_unit(hertz, formats=_HERTZ_FORMATS, **kwargs)


_VOLTS_FORMATS = [
    [0.0000001, 1000000000, "nanovolts", "nV"],
    [0.001, 1000000, "microvolts", "μV"],
    [1, 1000, "millivolts", "mV"],
    [math.inf, 1, "volts", "V"],
]


def format_volts(volts, **kwargs):
    return _format_unit(volts, formats=_VOLTS_FORMATS, **kwargs)
