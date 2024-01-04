# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""
Classes for dealing with waveform measurements and comparisons.
"""

from contextlib import contextmanager
import dataclasses
import json
import math
import functools
from os import PathLike
import pathlib
from typing import IO, Any, BinaryIO, Generator, TextIO

import numpy as np
from numpy.typing import NDArray
from PIL import Image, ImageDraw, ImageChops


@dataclasses.dataclass(kw_only=True, slots=True, frozen=True)
class Waveform:
    vertical_resolution: int
    vertical_division: float
    vertical_offset: float
    vertical_max: float
    vertical_min: float
    time_division: float
    trigger_offset: float
    sample_rate: float
    sample_step: int
    frequency: float
    data: NDArray[np.float64]

    @property
    def time_data(self):
        return self.data[:, 0]

    @property
    def voltage_data(self):
        return self.data[:, 1]

    @property
    def num_samples(self):
        return self.data.shape[0]

    @property
    def start_time(self):
        return self.time_data.min()

    @property
    def end_time(self):
        return self.time_data.max()

    @property
    def time_span(self):
        return self.time_data.max() - self.time_data.min()

    @property
    def min_voltage(self):
        return self.voltage_data.min()

    @property
    def max_voltage(self):
        return self.voltage_data.max()

    @property
    def voltage_span(self):
        return self.voltage_data.max() - self.voltage_data.min()

    def to_list(self, samples=None):
        if samples is not None:
            data = np.column_stack(
                (
                    _resample(self.data[:, 0], samples),
                    _resample(self.data[:, 1], samples),
                )
            )
        else:
            data = self.data

        return data.tolist()

    def to_binary_image(self, *, size: tuple[int, int] = (0, 0), thickness=1):
        w, h = size
        if w <= 0:
            w = self.num_samples * 2
        if h <= 0:
            h = self.vertical_resolution * 2

        im = Image.new("1", (w, h), color=0)
        draw = ImageDraw.Draw(im)

        lines = _map_series_to_image_coords(
            series=self.data[:, 1],
            src_min=self.vertical_min,
            src_max=self.vertical_max,
            dst_width=w,
            dst_height=h,
        )

        draw.line(
            lines.flatten().tolist(),
            fill=1,
            width=thickness,
            joint="curve",
        )

        return im

    def to_dict(self):
        result = {}

        for f in dataclasses.fields(self):
            value = getattr(self, f.name)

            if isinstance(value, np.ndarray):
                value = value.tolist()

            result[f.name] = value

        return result

    @classmethod
    def from_dict(cls, data):
        data["data"] = np.array(data["data"], dtype=np.float64)
        return cls(**data)

    def save(self, dst: str | PathLike | TextIO):
        with open_or_io(dst, "w") as fh:
            json.dump(self.to_dict(), fh)

    @classmethod
    def load(cls, dst: str | PathLike | TextIO):
        with open_or_io(dst, "r") as fh:
            data = json.load(fh)
        return cls.from_dict(data)


@contextmanager
def open_or_io(
    dst: str | PathLike | TextIO | BinaryIO, mode="w"
) -> Generator[IO[Any], Any, None]:
    if isinstance(dst, (str, pathlib.Path, PathLike)):
        dst = pathlib.Path(dst)
        with dst.open(mode) as fh:
            yield fh
    else:
        yield dst


class WaveformSimilarity:
    # See https://stackoverflow.com/questions/20644599/similarity-between-two-signals-looking-for-simple-measure

    def __init__(self, reference, other):
        self.reference = reference
        self.other = other

    @functools.cached_property
    def time(self):
        ref_time = np.correlate(
            self.reference.voltage_data, self.reference.voltage_data
        )
        inp_time = np.correlate(self.reference.voltage_data, self.other.voltage_data)
        return abs(ref_time - inp_time)[0]

    @functools.cached_property
    def frequency(self):
        ref_fft = np.fft.fft(self.reference.voltage_data)
        ref_freq = np.correlate(ref_fft, ref_fft)
        inp_freq = np.correlate(ref_fft, np.fft.fft(self.other.voltage_data))
        return abs(ref_freq - inp_freq)[0]

    @functools.cached_property
    def power(self):
        ref_power = np.sum(self.reference.voltage_data**2)
        inp_power = np.sum(self.other.voltage_data**2)
        return abs(ref_power - inp_power)


class WaveformPassFail:
    """Basic implementation of the common "Pass/Fail Mask" feature of
    oscilloscopes."""

    def __init__(
        self,
        *,
        resolution: tuple[int, int] = (0, 0),
    ):
        self.resolution = resolution
        self.reference_image = None

    def add_reference(self, reference, *, tolerance=0.1):
        ref_img = reference.to_binary_image(
            size=self.resolution,
            thickness=math.ceil(reference.num_samples * tolerance),
        )

        if not self.reference_image:
            self.reference_image = ref_img
            self.resolution = self.reference_image.size
        else:
            self.reference_image = ImageChops.logical_or(self.reference_image, ref_img)

    def compare(self, wf: Waveform):
        measured = wf.to_binary_image(
            size=self.resolution,
            thickness=1,
        )

        outside = ImageChops.subtract(measured, self.reference_image)

        return WaveformPassFailResult(
            reference_image=self.reference_image,
            measured_image=measured,
            outside_image=outside,
        )

    def save_as_image(self, dst):
        self.reference_image.save(dst)

    @classmethod
    def load_from_image(cls, src):
        inst = WaveformPassFail()
        img = Image.open(src).convert("1")
        inst.resolution = img.size
        inst.reference_image = img
        return inst


@dataclasses.dataclass(frozen=True, slots=True)
class WaveformPassFailResult:
    reference_image: Image.Image
    measured_image: Image.Image
    outside_image: Image.Image

    @property
    def composite_image(self):
        composite = Image.new(
            "RGBA",
            self.reference_image.size,
            color=(0, 0, 0, 255),
        )

        draw = ImageDraw.Draw(composite)
        draw.bitmap((0, 0), self.reference_image, (60, 100, 60, 255))
        draw.bitmap((0, 0), self.measured_image, (255, 255, 255, 255))
        draw.bitmap((0, 0), self.outside_image, (255, 100, 100, 255))

        return composite


def _resample(src: np.ndarray, num_samples: int):
    new_x = np.linspace(0, src.size - 1, num_samples)
    resampled = np.interp(new_x, np.arange(src.size), src)
    return resampled


def _map_series_to_image_coords(
    *,
    series: np.ndarray,
    src_min: float,
    src_max: float,
    dst_width: int,
    dst_height: int,
):
    # There has to be a better way to do this, but I'm too dumb to figure it out
    y_src_space = np.linspace(src_min, src_max, dst_height)
    y_dst_space = np.arange(dst_height)

    y_coords = np.array(dst_height) - np.interp(
        series, y_src_space, y_dst_space
    ).astype(int)

    x_src_space = np.linspace(0, dst_width, series.shape[0])
    x_dst_space = np.arange(dst_width)
    x_to_y_coords = np.interp(x_dst_space, x_src_space, y_coords).astype(int)

    return np.column_stack((x_dst_space, x_to_y_coords))
