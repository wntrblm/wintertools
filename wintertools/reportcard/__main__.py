# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import argparse
import pathlib
import pickle

import rich

from wintertools.reportcard import render

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=pathlib.Path)
    parser.add_argument("--html", type=pathlib.Path)
    parser.add_argument("--image", type=pathlib.Path)

    args = parser.parse_args()

    with args.source.open("rb") as fh:
        report = pickle.load(fh)

    rich.print(report)

    if args.html:
        render.render_html(report, args.html)

    if args.image:
        render.render_image(report, args.image)
