# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""Utilities for Terminal UIs."""

import atexit
import io
import math
import shutil
import sys

from wcwidth import wcswidth


def pad(spec, string):
    justify, count = spec[0], int(spec[1:])

    width = wcswidth(string) if string else 0
    spaces = " " * max(0, count - width)

    if justify == "<":
        return f"{string}{spaces}"
    if justify == ">":
        return f"{spaces}{string}"
    if justify == "^":
        left, right = spaces[: len(spaces) // 2], spaces[len(spaces) // 2 :]
        return f"{left}{string}{right}"


class Escape:
    CSI = "\u001b["
    ERASE_LINE = f"{CSI}2K\r"
    MOVE_UP = f"{CSI}1A"
    CURSOR_PREVIOUS_LINE = f"{CSI}1F"
    CURSOR_PREVIOUS_LINE_NUM = f"{CSI}{{count}}F"
    ERASE_AFTER_CURSOR = f"{CSI}0J"
    HIDE_CURSOR = f"{CSI}?25l"
    SHOW_CURSOR = f"{CSI}?25h"

    RESET = f"{CSI}0m"
    COLOR24FG = f"{CSI}38;2;{{r}};{{g}};{{b}}m"
    COLOR24BG = f"{CSI}48;2;{{r}};{{g}};{{b}}m"
    BOLD = f"{CSI}1m"
    FAINT = f"{CSI}2m"
    ITALIC = f"{CSI}3m"
    UNDERLINE = f"{CSI}4m"
    INVERT = f"{CSI}7m"
    STRIKETHROUGH = f"{CSI}9m"
    NORMAL = f"{CSI}22m"
    OVERLINED = f"{CSI}53m"


def _normalize_color(r, g=None, b=None):
    if isinstance(r, tuple):
        r, g, b = r

    if r > 1 or g > 1 or b > 1:
        r, g, b = r / 255, g / 255, b / 255

    return r, g, b


def gradient(a, b, v):
    a = _normalize_color(a)
    b = _normalize_color(b)

    v = max(0.0, min(v, 1.0))
    r = a[0] + v * (b[0] - a[0])
    g = a[1] + v * (b[1] - a[1])
    b = a[2] + v * (b[2] - a[2])
    return r, g, b


def gradient_text(string, start, end):
    result = ""
    for n, c in enumerate(string):
        color = gradient(start, end, n / len(string))
        result += rgb(color) + c
    return result


class Colors:
    reset = Escape.RESET

    @staticmethod
    def rgb(r, g=None, b=None, fg=True):
        r, g, b = _normalize_color(r, g, b)
        r, g, b = [int(x * 255) for x in (r, g, b)]

        if fg:
            return Escape.COLOR24FG.format(r=r, g=g, b=b)
        else:
            return Escape.COLOR24BG.format(r=r, g=g, b=b)


_stdout_stack = []
_updateable_stack = []


class Updateable:
    def __init__(self, clear_all=True, persist=True):
        self._buf = io.StringIO()
        self._line_count = 0
        self._clear_all = clear_all
        self._persist = persist

    def write(self, text):
        self._buf.write(text)

    def reset(self):
        self._line_count = 0

    def _erase(self, line_count):
        if line_count == 0:
            return

        clear_lines = Escape.CURSOR_PREVIOUS_LINE_NUM.format(count=line_count)
        if self._clear_all:
            clear_lines += Escape.ERASE_AFTER_CURSOR
        clear_lines += "\r"
        sys.__stdout__.write(clear_lines)

    def update(self):
        self._erase(self._line_count)
        self._line_count = 0

        output = self._buf.getvalue()
        sys.__stdout__.write(output)
        sys.__stdout__.flush()
        self._buf.truncate(0)
        self._line_count = output.count("\n")

    def __enter__(self, stdout=True):
        sys.stdout.write(Escape.HIDE_CURSOR)
        if stdout:
            _stdout_stack.append(sys.stdout)
            sys.stdout = self._buf

        if _updateable_stack:
            _updateable_stack[-1].update()
        _updateable_stack.append(self)

        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        sys.__stdout__.write(Escape.SHOW_CURSOR)

        if self._persist:
            output = self._buf.getvalue()
            sys.__stdout__.write(output)
            sys.__stdout__.flush()
        else:
            self._erase(self._line_count)
            self._line_count = 0

        self._buf.truncate(0)

        if sys.stdout == self._buf:
            sys.stdout = _stdout_stack.pop()

        _updateable_stack.pop()

    def flush(self):
        sys.__stdout__.flush()


class Segment:
    FILL_CHAR = "▓"

    def __init__(self, width, color=(1.0, 1.0, 1.0), char="▓"):
        self.width = width
        self.color = color
        self.char = char


class Bar:
    FILL_CHAR = "░"
    FILL_COLOR = (0.4, 0.4, 0.4)

    def __init__(self, width=50, fill=True):
        self.width = width
        self.fill = fill

    def draw(self, *segments, end="\n", file=None):
        if file is None:
            file = sys.stdout

        segments = list(segments)

        for n, segment in enumerate(segments):
            if isinstance(segment, tuple):
                segments[n] = Segment(*segment)

        # Add end segment if needed.
        if self.fill:
            left_to_fill = 1.0 - sum(s.width for s in segments)
            segments.append(
                Segment(left_to_fill, color=self.FILL_COLOR, char=self.FILL_CHAR)
            )

        # Largest remainder method allocation
        seg_lengths = [math.floor(s.width * self.width) for s in segments]
        seg_fract = [(n, (s.width * self.width) % 1.0) for n, s in enumerate(segments)]
        seg_fract.sort(key=lambda x: x[1], reverse=True)
        remainder = self.width - sum(seg_lengths)

        for n in range(remainder):
            seg_lengths[seg_fract[n][0]] += 1

        # Now draw
        buf = ""
        for n, seg in enumerate(segments):
            buf += Colors.rgb(*seg.color) + (seg.char * seg_lengths[n])
        buf += Colors.reset + end

        file.write(buf)


class Columns:
    def __init__(self, *columns):
        self._columns = columns

    def draw(self, *values, file=None):
        if file is None:
            file = sys.stdout

        n = 0
        for v in values:
            if isinstance(v, str) and v.startswith(Escape.CSI):
                file.write(v)
                continue
            if isinstance(v, tuple) and len(v) == 3:
                file.write(Colors.rgb(v))
                continue

            spec = self._columns[n]
            padded = pad(spec, f"{v}")
            file.write(padded)

            n += 1

        file.write(Colors.reset + "\n")

    def __len__(self):
        return sum(int(s[1:]) for s in self._columns)


def width():
    columns, lines = shutil.get_terminal_size()
    return columns


def reset_terminal():
    print(Escape.RESET + Escape.SHOW_CURSOR, end="")
    sys.__stdout__.flush()


atexit.register(reset_terminal)


# Helpful aliases

rgb = Colors.rgb
reset = Escape.RESET
bold = Escape.BOLD
faint = Escape.FAINT
italic = Escape.ITALIC
underline = Escape.UNDERLINE
invert = Escape.INVERT
strikethrough = Escape.STRIKETHROUGH
normal = Escape.NORMAL
overlined = Escape.OVERLINED
