# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import colorsys
import math
from typing import Callable, Sequence, Union

import pydantic
import rich.align
import rich.box
import rich.table
import rich.text

from wintertools.units import format_hertz, format_volts
from wintertools.waveform import Waveform

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


class Outline(pydantic.BaseModel):
    left: float | None = 5
    right: float | None = None
    top: float | None = None
    bottom: float | None = 5


class GridLines(pydantic.BaseModel):
    x_step: float | None = None
    y_step: float | None = None

    def draw(self, dwg, x_axis, y_axis, w, h):
        px = dwg.path(class_="x-axis grid-lines")
        px.fill(color="none")
        px.stroke(color="gray", width=1)
        py = dwg.path(class_="y-axis grid-lines")
        py.fill(color="none")
        py.stroke(color="gray", width=1)

        # Vertical lines
        if self.x_step is None:
            self.x_step = 0.1

        print(f"{self.x_step=}")

        x_center = x_axis.offset_of(0)
        x_min_step = -math.floor(x_center / self.x_step)
        x_max_step = math.ceil((1 - x_center) / self.x_step)

        for step in range(x_min_step, x_max_step):
            x = x_center + (step * self.x_step)
            px.push("M", x_axis.ease(x) * w, 0)
            px.push("l", 0, h)

        # Horizontal lines
        if self.y_step is None:
            self.y_step = 0.1

        y_center = y_axis.offset_of(0)
        y_min_step = -math.floor(y_center / self.y_step)
        y_max_step = math.ceil((1 - y_center) / self.y_step)

        for step in range(y_min_step, y_max_step):
            y = y_center + (step * self.y_step)
            py.push("M", 0, h - y_axis.ease(y) * h)
            py.push("l", w, 0)

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
    outline: Outline = pydantic.Field(default_factory=Outline)

    @classmethod
    def from_waveform(cls, wf: Waveform, *, label=None):
        if label is None:
            label = f"{format_volts(wf.voltage_span, precision=1)} @ {format_hertz(wf.frequency, precision=1)}"

        return cls(
            height=600,
            x_axis=Axis(
                min=wf.start_time,
                max=wf.end_time,
                label=label,
            ),
            y_axis=Axis(min=wf.vertical_min, max=wf.vertical_max),
            padding=Padding(left=50, right=50, top=10, bottom=100),
            outline=Outline(top=5, left=5, right=5, bottom=5),
            center_line=True,
        )

    def draw(self, series: Union[Series, Sequence[Series]]):
        drawing = Drawing(self.width, self.height)
        drawing.add_builtin_stylesheet("graph.css")
        svg = drawing.svg
        x, y, w, h = self.padding(0, 0, drawing.width, drawing.height)
        h_half = h * 0.5

        clip_path = svg.defs.add(svg.clipPath(id="clipBounds"))
        clip_path.add(svg.rect(insert=(x, y), size=(w, h)))

        g = svg.g()
        g.translate(x, y)
        svg.add(g)

        # middle line
        if self.center_line is not False:
            p = svg.path()
            p.fill(color="none")
            p.stroke(color="black", width=2)
            # p.dasharray([4])
            center_y = self.y_axis.offset_of(0)
            center_y = h - (center_y * h)
            p.push("M", 0, center_y)
            p.push("L", w, center_y)
            g.add(p)

        # gridlines
        for p in self.grid_lines.draw(svg, self.x_axis, self.y_axis, w, h):
            g.add(p)

        # Series
        if isinstance(series, Series):
            serieses = [series]
        else:
            serieses = series

        # separate (nested) group for series so we can clip it.
        clip_g = svg.add(svg.g(clip_path="url(#clipBounds)"))
        g2 = clip_g.add(svg.g())
        g2.translate(x, y)

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
                y_offset_factor = min(1.0, max(0.0, y_offset_factor))
                y_offset = h - (y_offset_factor * h)

                p.push("M" if n == 0 else "L", x_offset, y_offset)

            g2.add(p)

        # outlines
        if self.outline.left is not None:
            p = svg.path()
            p.fill(color="none")
            p.stroke(color="black", width=self.outline.left)
            p.push("M", 0, 0)
            p.push("l", 0, h)
            g.add(p)
        if self.outline.bottom is not None:
            p = svg.path()
            p.fill(color="none")
            p.stroke(color="black", width=self.outline.bottom)
            p.push("M", 0, h)
            p.push("l", w, 0)
            g.add(p)
        if self.outline.right is not None:
            p = svg.path()
            p.fill(color="none")
            p.stroke(color="black", width=self.outline.right)
            p.push("M", w, 0)
            p.push("l", 0, h)
            g.add(p)
        if self.outline.top is not None:
            p = svg.path()
            p.fill(color="none")
            p.stroke(color="black", width=self.outline.top)
            p.push("M", 0, 0)
            p.push("l", w, 0)
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

        table = rich.table.Table(
            expand=False,
            box=rich.box.MINIMAL,
            border_style="rgb(100,100,100)",
        )
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

        return rich.align.Align.center(table)


def _color_for_value(val, min, max):
    span = max - min
    dist = (val - min) / span

    if 0 <= dist <= 1:
        hue = 0.6 - dist * 0.4
    else:
        hue = 0

    rgbstr = ",".join([str(int(n * 255)) for n in colorsys.hsv_to_rgb(hue, 0.6, 1.0)])

    return f"rgb({rgbstr})"
