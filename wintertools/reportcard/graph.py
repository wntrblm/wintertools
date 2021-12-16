# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import colorsys
from typing import Callable, Sequence, Union

import pydantic
import rich.table
import rich.text

from .svg import Drawing


def _text(dwg, x, y, content, class_=""):
    lg = dwg.g()
    lg.translate(x, y)
    lg.add(
        dwg.text(
            content,
            class_=class_,
        )
    )
    return lg


class Ease:
    @staticmethod
    def linear(x):
        return x

    @staticmethod
    def quad(x):
        return x * x

    @staticmethod
    def cube(x):
        return x * x * x

    @staticmethod
    def quart(x):
        return x * x * x * x


class Axis(pydantic.BaseModel):
    label: str = ""
    min: float = 0.0
    min_label: str = ""
    max: float = 1.0
    max_label: str = ""
    ease: Callable[[float], float] = Ease.linear

    @property
    def span(self):
        return self.max - self.min

    def offset_of(self, val):
        norm = (val - self.min) / self.span
        return self.ease(norm)


class Padding(pydantic.BaseModel):
    left: float = 0
    right: float = 0
    top: float = 0
    bottom: float = 0

    def x(self, x):
        return x + self.left

    def y(self, y):
        return y + self.top

    def width(self, w):
        return w - (self.left + self.right)

    def height(self, h):
        return h - (self.top + self.bottom)

    def __call__(self, x, y, w, h):
        return self.x(x), self.y(y), self.width(w), self.height(h)


class GridLines(pydantic.BaseModel):
    x_step: float = None
    y_step: float = None

    def draw(self, dwg, x_axis, y_axis, w, h):
        px = dwg.path(class_="x-axis grid-lines")
        px.fill(color="none")
        px.stroke(color="gray", width=1)
        py = dwg.path(class_="y-axis grid-lines")
        py.fill(color="none")
        py.stroke(color="gray", width=1)

        # Vertical lines
        if self.x_step is None:
            self.x_step = 1 / x_axis.span

        x = self.x_step

        while x < 1.0:
            px.push("M", x_axis.ease(x) * w, 0)
            px.push("l", 0, h)
            x += self.x_step

        # Horizontal lines
        if self.y_step is None:
            self.y_step = 1 / y_axis.span

        y = self.y_step

        while y <= 1.0:
            py.push("M", 0, y_axis.ease(y) * h)
            py.push("l", w, 0)
            y += self.y_step

        return [px, py]


class Series(pydantic.BaseModel):
    data: Sequence[tuple[float, float]] = []
    stroke: str = "black"
    stroke_width: int = 8


class LineGraph(pydantic.BaseModel):
    width: int = 1000
    height: int = 1000
    padding: Padding = Padding(left=100, right=50, top=10, bottom=100)
    x_axis: Axis = pydantic.Field(default_factory=Axis)
    y_axis: Axis = pydantic.Field(default_factory=Axis)
    grid_lines: GridLines = pydantic.Field(default_factory=GridLines)
    center_line: bool = False

    def draw(self, series: Union[Series, Sequence[Series]]):
        drawing = Drawing(self.width, self.height)
        drawing.add_builtin_stylesheet("graph.css")
        svg = drawing.svg
        x, y, w, h = self.padding(0, 0, drawing.width, drawing.height)
        h_half = h * 0.5

        g = svg.g()
        g.translate(x, y)
        svg.add(g)

        # left and bottom lines
        p = svg.path()
        p.fill(color="none")
        p.stroke(color="black", width=5)
        p.push("M", 0, 0)
        p.push("l", 0, h)
        p.push("l", w, 0)
        g.add(p)

        # middle line
        if self.center_line:
            p = svg.path()
            p.fill(color="none")
            p.stroke(color="black", width=5)
            p.dasharray([4])
            p.push("M", 0, h_half)
            p.push("L", w, h_half)
            g.add(p)

        # gridlines
        for p in self.grid_lines.draw(svg, self.x_axis, self.y_axis, w, h):
            g.add(p)

        # Series
        if isinstance(series, Series):
            serieses = [series]
        else:
            serieses = series

        # start of data points
        for series in serieses:
            p = svg.path()
            p.fill(color="none")
            p.stroke(color=series.stroke, width=series.stroke_width)
            p.push("M", 0, h_half)

            # datapoints
            for n, (x, y) in enumerate(series.data):
                x_offset_factor = self.x_axis.offset_of(x)
                x_offset_factor = min(1.0, max(0.0, x_offset_factor))
                x_offset = x_offset_factor * w

                y_offset_factor = self.y_axis.offset_of(y)
                x_offset_factor = min(1.0, max(0.0, y_offset_factor))
                y_offset = h - (x_offset_factor * h)

                p.push("M" if n == 0 else "L", x_offset, y_offset)

            g.add(p)

        # Labels
        g.add(_text(svg, w / 2, h, self.x_axis.label, "axis x-axis label"))
        g.add(_text(svg, 0, h, self.x_axis.min_label, "axis x-axis range-min"))
        g.add(_text(svg, w, h, self.x_axis.max_label, "axis x-axis range-max"))

        g.add(_text(svg, 0, h / 2, self.y_axis.label, class_="axis y-axis label"))
        g.add(_text(svg, 0, 0, self.y_axis.max_label, "axis y-axis range-max"))
        g.add(_text(svg, 0, h, self.y_axis.min_label, "axis y-axis range-min"))

        return drawing.data_url

    def draw_console(self, series):
        if isinstance(series, Series):
            series = [series]

        table = rich.table.Table()
        table.add_column(self.x_axis.label)

        for _ in series:
            table.add_column(self.y_axis.label)

        for n in range(len(series[0].data)):
            row = [series[0].data[n][0]]

            for s in series:
                row.append(s.data[n][1])

            for n, v in enumerate(row):
                if n == 0:
                    row[n] = rich.text.Text(f"{v:0.3f}", style="bold italic")
                elif isinstance(v, float):
                    color = _color_for_value(v, self.y_axis.min, self.y_axis.max)
                    row[n] = rich.text.Text(f"{v:0.3f}", style=color)
                else:
                    row[n] = f"{v!r}"

            table.add_row(*row)

        return table


def _color_for_value(val, min, max):
    span = max - min
    dist = (val - min) / span

    if 0 <= dist <= 1:
        hue = 0.6 - dist * 0.4
    else:
        hue = 0

    rgbstr = ",".join([str(int(n * 255)) for n in colorsys.hsv_to_rgb(hue, 0.6, 1.0)])

    return f"rgb({rgbstr})"
