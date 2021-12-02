# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import datetime
from typing import Union, Sequence


import pydantic

from . import graph


class Item(pydantic.BaseModel):
    type: str = "unknown"
    class_: str = ""


class TextItem(Item):
    type: str = "text"
    text: str


class LabelValueItem(Item):
    type: str = "label_value"
    label: str
    value: str


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


class Section(pydantic.BaseModel):
    name: str
    items: list[Item]


class Report(pydantic.BaseModel):
    name: str
    ulid: str
    date: datetime.datetime = pydantic.Field(default_factory=datetime.datetime.now)
    sections: list[Section]
