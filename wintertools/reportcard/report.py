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

from . import graph

_MAX_CONSOLE_WIDTH = 60


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
            rich.text.Text(character, style=style),
        )


class ImageItem(Item):
    type: str = "image"
    src: str


class LineGraphItem(Item):
    type: str = "line_graph"
    series: Union[graph.Series, Sequence[graph.Series]]
    graph: graph.LineGraph

    @property
    def src(self):
        return self.graph.draw(series=self.series)

    def __rich__(self):
        return self.graph.draw_console(series=self.series)


class Section(_BaseModel):
    name: str
    items: list[Item] = []

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

    @property
    def succeeded(self):
        for s in self.sections:
            for i in s.items:
                if isinstance(i, PassFailItem):
                    if not i.value:
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

        if not self.succeeded:
            renderables.append(rich.panel.Panel.fit("[bold flashing red]FAILED TEST"))

        return rich.align.Align.center(
            rich.panel.Panel.fit(
                rich.console.Group(*renderables, fit=True), width=_MAX_CONSOLE_WIDTH
            )
        )
