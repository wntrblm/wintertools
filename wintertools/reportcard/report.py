# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import datetime
import pathlib
import pickle
from typing import Union, Sequence

import pydantic
import rich
import rich.text
import rich.console
import rich.padding
import rich.panel
import ulid

from . import graph


class Item(pydantic.BaseModel):
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
        return rich.text.Text(f"{self.label}: [bold]{self.value}[/bold]")


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
        return rich.text.Text(f"{self.label}: {character}", style=style)


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


class Section(pydantic.BaseModel):
    name: str
    items: list[Item] = []

    def __rich__(self):
        return rich.console.Group(
            rich.padding.Padding(
                rich.text.Text(self.name, style="bold underline"), (1, 0),
            ),
            *self.items
        )


class Report(pydantic.BaseModel):
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
            file = f"{self.name.lower()}-{self.ulid}.pickle"

        if isinstance(file, (str, pathlib.Path)):
            with open(file, "wb") as fh:
                pickle.dump(self, fh)
            rich.print(f"[green]Report saved to {file}")
        elif file:
            pickle.dump(self, fh)

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
            renderables.append(
                rich.panel.Panel.fit("[bold flashing red]FAILED TEST")
            )

        return rich.console.Group(*renderables)
