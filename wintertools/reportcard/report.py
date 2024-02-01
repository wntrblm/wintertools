# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import datetime
import inspect
import json
import pathlib
import textwrap
import types
from typing import Sequence, Union

import pydantic
import rich
import rich.align
import rich.console
import rich.padding
import rich.panel
import rich.text
import ulid
import numpy as np

from wintertools.waveform import Waveform
from . import graph

_MAX_CONSOLE_WIDTH = 120
BLACKISH = "#231F20"
TEALS = (
    "#99D1D6",
    "#66ADB5",
    "#408C94",
    "#267880",
)
REDS = (
    "#F597A3",
    "#F2727F",
    "#DB475B",
    "#C02435",
)
PURPLES = (
    "#C7B8ED",
    "#A38AD6",
    "#7D61BA",
    "#5E409E",
)
COLORS = np.array([TEALS, REDS, PURPLES]).T.flatten()
DEFAULT_STROKES = (BLACKISH, TEALS[-1], REDS[-1], PURPLES[-1])


def _json_encoder(val, default):
    if isinstance(val, datetime.datetime):
        return dict(__datetime__=True, value=val.isoformat())
    if isinstance(val, pydantic.BaseModel):
        return val.dict()
    if inspect.isfunction(val):
        return dict(
            __function__=True,
            name=val.__name__,
            source=textwrap.dedent(str(inspect.getsource(val))),
        )

    return default(val)
    # raise ValueError(f"{val!r} ({type(val)!r}) is not json encodeable.")


def _json_decoder(val):
    if "__datetime__" in val:
        return datetime.datetime.fromisoformat(val["value"])
    if "__function__" in val:
        module = types.ModuleType("__dynamic")
        compiled = compile(val["source"], "", "exec")
        exec(compiled, module.__dict__)
        return module.__dict__[val["name"]]
    if "__class__" in val:
        type_ = val["__class__"]
        if type_ == "TextItem":
            return TextItem(**val)
        if type_ == "SubTextItem":
            return SubTextItem(**val)
        if type_ == "LabelValueItem":
            return LabelValueItem(**val)
        if type_ == "PassFailItem":
            return PassFailItem(**val)
        if type_ == "ImageItem":
            return ImageItem(**val)
        if type_ == "LineGraphItem":
            return LineGraphItem(**val)

    return val


def _json_dumps(val, *, default):
    return json.dumps(val, default=lambda v: _json_encoder(v, default), indent=2)


def _json_loads(val):
    return json.loads(val, object_hook=_json_decoder)


class _BaseModel(pydantic.BaseModel):
    """Extended to return the class name when serializing"""

    class Config:
        json_loads = _json_loads
        json_dumps = _json_dumps

    def _iter(
        self,
        to_dict: bool = False,
        by_alias: bool = False,
        include=None,
        exclude=None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ):
        yield "__class__", self.__class__.__name__
        for k, v in super()._iter():
            yield k, v


class Item(_BaseModel):
    type: str = "unknown"
    class_: str = ""

    @property
    def succeeded(self):
        return True

    def __rich__(self):
        return rich.text.Text(f"<no renderer for {self.type}>", style="yellow italic")


class TextItem(Item):
    type: str = "text"
    text: str

    def __rich__(self):
        return rich.text.Text(self.text)


class SubTextItem(Item):
    type: str = "text"
    text: str
    class_: str = "font-weight-normal"

    def __rich__(self):
        return rich.text.Text(self.text, style="italic")


class LabelValueItem(Item):
    type: str = "label_value"
    label: str
    value: str

    def __rich__(self):
        return rich.console.Group(
            rich.text.Text(f"{self.label}: ", style="italic", end=""),
            rich.text.Text(f"{self.value}", style="bold"),
        )


class PassFailItem(Item):
    type: str = "pass_fail"
    label: str
    value: bool
    details: str = ""

    @property
    def succeeded(self):
        return self.value

    @property
    def icon(self):
        if self.value:
            return "check_circle"
        else:
            return "error_outline"

    def __rich__(self):
        style = "green" if self.value else "bold red"
        character = "✓" if self.value else "❌"
        return rich.console.Group(
            rich.text.Text(f"{self.label}: ", style="italic", end=""),
            rich.text.Text(f"{self.details} {character}", style=style),
        )


class ImageItem(Item):
    type: str = "image"
    src: str


class LineGraphItem(Item):
    type: str = "line_graph"
    series: Union[graph.Series, Sequence[graph.Series]]
    graph: graph.LineGraph

    @classmethod
    def from_waveform(
        cls,
        wf: Waveform | list[Waveform],
        *,
        label=None,
        points=200,
        stroke: str | list[str] | None = None,
        stroke_width=6,
    ):
        if stroke is None:
            stroke = DEFAULT_STROKES

        wfs = [wf] if isinstance(wf, Waveform) else wf
        strokes = [stroke] if isinstance(stroke, str) else stroke

        return LineGraphItem(
            series=[
                graph.Series(
                    data=wf.to_list(points),
                    stroke=strokes[n % len(strokes)],
                    stroke_width=stroke_width,
                )
                for n, wf in enumerate(wfs)
            ],
            graph=graph.LineGraph.from_waveform(wfs[0], label=label),
        )

    @property
    def src(self):
        return self.graph.draw(series=self.series)

    def __rich__(self):
        return self.graph.draw_console(series=self.series)


class Section(_BaseModel):
    name: str
    items: list[Item] = []

    def append(self, item):
        self.items.append(item)
        return item

    def extend(self, seq):
        self.items.extend(seq)

    @property
    def succeeded(self):
        for i in self.items:
            if not i.succeeded:
                return False
        return True

    def __rich__(self):
        return rich.console.Group(
            rich.padding.Padding(
                rich.text.Text(self.name, style="cyan bold underline"),
                (1, 0),
            ),
            *self.items,
        )


class Report(_BaseModel):
    name: str
    ulid: str = pydantic.Field(default_factory=lambda: str(ulid.ULID()))
    date: datetime.datetime = pydantic.Field(default_factory=datetime.datetime.now)
    sections: list[Section] = []

    def append(self, item):
        self.sections.append(item)

    def extend(self, seq):
        self.sections.extend(seq)

    def __getitem__(self, index: str) -> Section | None:
        for s in self.sections:
            if s.name == index:
                return s
        return None

    @property
    def succeeded(self):
        for s in self.sections:
            if not s.succeeded:
                return False
        return True

    def save(self, file=None):
        if file is None:
            file = pathlib.Path(f"reports/{self.name.lower()}-{self.ulid}.json")
            file.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(file, (str, pathlib.Path)):
            with open(file, "w") as fh:
                fh.write(self.json())
            rich.print(f"[green]Report saved to {file}")
            return pathlib.Path(file)
        elif file:
            file.write(self.json())

    @classmethod
    def load(self, file):
        if isinstance(file, (str, pathlib.Path)):
            with open(file, "r") as fh:
                return self.parse_raw(fh.read())
        elif file:
            return self.parse_raw(file.read())

    def __rich__(self):
        name_color = "green" if self.succeeded else "red"

        renderables = [
            rich.padding.Padding(
                rich.text.Text(self.name, style=f"{name_color} bold underline"), (1, 0)
            ),
            rich.text.Text(self.ulid, style=""),
            rich.text.Text(f"{self.date.isoformat()}", style="italic"),
            *self.sections,
        ]

        if self.succeeded:
            renderables.append(
                rich.align.Align.center(
                    rich.padding.Padding(
                        "SUCCEEDED",
                        pad=(1, 5),
                        style="bold black on green",
                        expand=True,
                    )
                )
            )
        else:
            renderables.append(
                rich.align.Align.center(
                    rich.padding.Padding(
                        "FAILED",
                        pad=(1, 5),
                        style="bold white on red",
                        expand=True,
                    )
                )
            )

        return rich.panel.Panel.fit(
            rich.console.Group(
                *renderables,
                fit=True,
            ),
            width=_MAX_CONSOLE_WIDTH,
        )
