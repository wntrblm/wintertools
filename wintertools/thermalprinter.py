# Copyright (c) 2022 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import subprocess
import sys

try:
    import phomemo_m02s
    import phomemo_m02s.printer
except ImportError:
    phomemo_m02s = None

from . import config
from .print import print


def print_via_serial(image):
    port = config.get("thermalprinter.port", default="/dev/tty.M02S")
    print(f"Printing to thermal printer on {port}")

    printer = phomemo_m02s.printer.Printer(port)
    printer.initialize()
    printer.reset()
    printer.align_center()

    printer.print_image(image, width=phomemo_m02s.printer.Printer.MAX_WIDTH)

    printer.reset()


def print_via_cups(image):
    printer_name = config.get("thermalprinter.name", prompt_if_missing=True)

    print(f"Printing to {printer_name}")

    subprocess.run(["lp", "-d", printer_name, image])


def print_me_maybe(image):
    if not config.get("thermalprinter.should_print", prompt_if_missing=True):
        return

    printer_type = config.get("thermalprinter.type", prompt_if_missing=True)

    if printer_type == "serial":
        print_via_serial(image)
    else:
        print_via_cups(image)


if __name__ == "__main__":
    print_me_maybe(sys.argv[1])
