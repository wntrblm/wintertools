#!/usr/bin/env python3

# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import argparse
import colorsys
import dataclasses
import json
import pathlib
import subprocess
import typing

from wintertools import tui

COLUMNS = tui.Columns("<15", ">10", "^5", ">10", ">7")
COLUMNS_ALT = tui.Columns("<15", ">10", "<13", ">9")
BAR = tui.Bar(width=len(COLUMNS))
FIXED_SEG_COLOR = (255, 158, 221)
GRADIENT_START = colorsys.hsv_to_rgb(188 / 360, 0.8, 1.0)
GRADIENT_END = colorsys.hsv_to_rgb(0.8, 0.8, 1.0)
PLUS_COLOR = (1.0, 1.0, 0.5)
MINUS_COLOR = (127, 255, 191)


def sizeof_fmt(num, suffix="B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return "%3.2f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.2f %s%s" % (num, "Yi", suffix)


def _color_for_percent(percentage):
    return tui.gradient(GRADIENT_START, GRADIENT_END, percentage)


def _analyze_elf(elf, size_prog):
    fw_size_output = subprocess.check_output([size_prog, "-A", "-d", elf])
    fw_size_output = fw_size_output.decode("utf-8").split("\n")[2:]
    sections = {}
    bootloader_size = 0

    for line in fw_size_output:
        if not line:
            continue
        parts = line.split(None)
        sections[parts[0]] = int(parts[1], 10)
        if parts[0] == ".text":
            bootloader_size = int(parts[2], 10)

    program_size = (
        sections[".text"] + sections.get(".relocate", 0) + sections.get(".data", 0)
    )
    stack_size = sections.get(".stack", 0)
    variables_size = (
        sections.get(".relocate", 0) + sections.get(".data", 0) + sections[".bss"]
    )

    return bootloader_size, program_size, stack_size, variables_size


@dataclasses.dataclass
class _MemorySection:
    name: str
    size: int
    last_size: typing.Optional[int] = None
    fixed: bool = False


def _print_memory_sections(name, size, human_readable, *sections):
    used = sum(s.size for s in sections)
    used_fixed = sum(s.size for s in sections if s.fixed)
    used_percent = used / size
    color = _color_for_percent(used_percent)

    COLUMNS.draw(
        f"{name} used:",
        color,
        f"{sizeof_fmt(used)}" if human_readable else f"{used:,}",
        tui.reset,
        "/",
        f"{sizeof_fmt(size)}" if human_readable else f"{size:,}",
        color,
        f"({round(used_percent * 100)}%)",
    )

    BAR.draw(
        tui.Segment(used_fixed / size, FIXED_SEG_COLOR),
        tui.Segment((used - used_fixed) / size, _color_for_percent(used_percent)),
    )

    for sec in sections:
        if sec.fixed:
            color = FIXED_SEG_COLOR
        else:
            color = _color_for_percent(sec.size / size)

        if sec.last_size is not None:
            diff = sec.size - sec.last_size
            if diff != 0:
                last_size_sec = (
                    MINUS_COLOR if diff < 0 else PLUS_COLOR,
                    f" {diff:+,}",
                    tui.reset,
                )
            else:
                last_size_sec = ("",)
        else:
            last_size_sec = ("",)

        COLUMNS_ALT.draw(
            color,
            f"{sec.name}: ",
            f"{sizeof_fmt(sec.size)}" if human_readable else f"{sec.size:,}",
            *last_size_sec,
            color,
            f"({round(sec.size / size * 100)}%)",
        )


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("elf_file", type=pathlib.Path)
    parser.add_argument("--flash-size", type=lambda x: int(x, 0))
    parser.add_argument("--ram-size", type=lambda x: int(x, 0))
    parser.add_argument("--bootloader-size", default=None)
    parser.add_argument("--no-last", type=bool, default=False)
    parser.add_argument("--size-prog", type=pathlib.Path, default="arm-none-eabi-size")
    parser.add_argument(
        "--human-readable",
        help="print sizes in human-readable format",
        action="store_true",
    )

    args = parser.parse_args()

    build_dir = args.elf_file.parent
    last_file = build_dir / "fw-size.last"

    if last_file.exists():
        last_data = json.loads(last_file.read_text())
        last_program_size = last_data["program_size"]
        last_variables_size = last_data["variables_size"]
    else:
        last_program_size = None
        last_variables_size = None

    bootloader_size, program_size, stack_size, variables_size = _analyze_elf(
        args.elf_file, args.size_prog
    )

    if args.bootloader_size:
        bootloader_size = int(args.bootloader_size)

    if last_file.exists():
        last_data = json.loads(last_file.read_text())

    _print_memory_sections(
        "Flash",
        args.flash_size,
        args.human_readable,
        _MemorySection(name="Bootloader", size=bootloader_size, fixed=True),
        _MemorySection(name="Program", size=program_size, last_size=last_program_size),
    )
    print()
    print()
    _print_memory_sections(
        "RAM",
        args.ram_size,
        args.human_readable,
        _MemorySection(name="Stack", size=stack_size, fixed=True),
        _MemorySection(
            name="Variables", size=variables_size, last_size=last_variables_size
        ),
    )

    if not args.no_last:
        last_file.write_text(
            json.dumps(
                dict(
                    program_size=program_size,
                    variables_size=variables_size,
                )
            )
        )


if __name__ == "__main__":
    main()
