# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import argparse
import pathlib

import rich

from wintertools.reportcard import render
from wintertools.reportcard.report import Report
from wintertools import thermalprinter


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=pathlib.Path)
    parser.add_argument("--html", type=pathlib.Path)
    parser.add_argument("--image", type=pathlib.Path)
    parser.add_argument("--print", action="store_true")

    args = parser.parse_args()

    with args.source.open("rb") as fh:
        report = Report.load(fh)

    rich.print(report)

    if args.html:
        render.render_html(report, args.html)

    if args.image:
        render.render_image(report, args.image)

    if args.print:
        dest = render.render_image(report, args.image)
        thermalprinter.print_me_maybe(dest)
