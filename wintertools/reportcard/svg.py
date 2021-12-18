# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import base64
import importlib.resources
import io

import svgwrite


class Drawing:
    def __init__(self, w, h):
        self.svg = svgwrite.Drawing(size=("100%", "100%"), debug=False)
        self.width = w
        self.height = h
        self.svg.viewbox(0, 0, w, h)

    def add_builtin_stylesheet(self, name):
        self.svg.embed_stylesheet(
            importlib.resources.read_text("wintertools.reportcard", name)
        )

    @property
    def data_url(self):
        io_ = io.StringIO()
        self.svg.write(io_)
        encoded = base64.b64encode(io_.getvalue().encode("utf-8")).decode("utf-8")
        return f"data:image/svg+xml;base64,{encoded}"
