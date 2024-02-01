# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""
Wrapper for talking to the Siglent SDS 1104X-E over VISA.

SCPI & Programming reference: https://storage.googleapis.com/files.winterbloom.com/docs/Programming%20Guide%20PG%2001%20E%2002%20C.pdf
"""
import time

import numpy as np

from . import visa
from .waveform import Waveform

_VERT_GRID_LINES = 25
_HORIZ_GRID_LINES = 14

class Oscilloscope(visa.Instrument):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._time_div = None

    def connect(self, *args, **kwargs):
        super().connect(*args, **kwargs)
        # Don't send command headers in responses, just the result.
        self.write("chdr off")

    def close(self):
        self.port.close()

    def reset(self):
        self.write("*rst")
        # *opc? should block until the device is ready, but it doesn't, so just sleep.
        time.sleep(4)
        self._time_div = None

    def enable_bandwidth_limit(self):
        self.write("BWL C1,ON,C2,ON,C3,ON,C4,ON")

    def set_intensity(self, grid: str, trace: str):
        self.write(f"intensity GRID,{grid},TRACE,{trace}")

    def enable_channel(self, trace: str):
        self.write(f"{trace}:trace on")

    def disable_channel(self, trace: str):
        self.write(f"{trace}:trace off")

    def get_vertical_division(self, trace: str):
        return float(self.query(f"{trace}:vdiv?"))

    def set_vertical_division(self, trace: str, volts: str):
        self.write(f"{trace}:vdiv {volts}")

    def get_vertical_offset(self, trace: str):
        return float(self.query(f"{trace}:ofst?"))

    def set_vertical_offset(self, channel: str, volts: str):
        self.write(f"{channel}:ofst {volts}")

    def set_ac_coupling(self, channel: str, impedance="1M"):
        self.write(f"{channel}:coupling A{impedance}")

    def set_dc_coupling(self, channel: str, impedance="1M"):
        self.write(f"{channel}:coupling D{impedance}")

    def get_time_division(self):
        return float(self.query("tdiv?"))

    def set_time_division(self, value: str, force: bool = False):
        # Prevent unnecessarily changing the time division, since it can
        # be slow.
        if self._time_div != value or force:
            self.write(f"tdiv {value}")
            self._time_div = value

    def get_trigger_delay(self):
        return float(self.query("trig_delay?"))

    def set_time_division_from_frequency(self, frequency: float, force: bool = False):
        if frequency > 1200:
            self.set_time_division("100us", force=force)
        elif frequency > 700:
            self.set_time_division("200us", force=force)
        elif frequency > 180:
            self.set_time_division("500us", force=force)
        elif frequency > 90:
            self.set_time_division("1ms", force=force)
        elif frequency > 46:
            self.set_time_division("2ms", force=force)
        else:
            self.set_time_division("5ms", force=force)

    def get_sample_rate(self):
        return float(self.query("sample_rate?"))

    def enable_cursors(self):
        self.write("cursor_measure manual")

    def set_cursor_type(self, type: str):
        self.write(f"cursor_type {type}")

    def set_vertical_cursor(self, trace: str, ref: float, dif: float):
        self.write(f"{trace}:cursor_set VREF,{ref},VDIF,{dif}")

    def get_cymometer(self):
        return float(self.query("cymometer?"))

    def get_parameter_value(self, trace: str, param: str):
        try:
            return float(self.query(f"{trace}:parameter_value? {param}").split(",")[-1])
        except ValueError:
            return 0

    def get_peak_to_peak(self, trace: str):
        return self.get_parameter_value(trace, "PKPK")

    def get_mean(self, trace: str):
        return self.get_parameter_value(trace, "MEAN")

    def get_max(self, trace: str):
        return self.get_parameter_value(trace, "MAX")

    def get_freq(self, trace: str):
        return self.get_parameter_value(trace, "FREQ")

    def set_trigger_level(self, trig_source: str, trig_level: str):
        self.write(f"{trig_source}:trig_level {trig_level}")

    def show_measurement(self, trace: str, parameter: str):
        self.write(f"parameter_custom {trace},{parameter}")

    def get_waveform(self, trace: str, step: int = 1, count: int = 0, first: int = 0):
        vdiv = self.get_vertical_division(trace)
        voffset = self.get_vertical_offset(trace)
        tdiv = self.get_time_division()
        trigdelay = self.get_trigger_delay()
        sample_rate = self.get_sample_rate()
        freq = self.get_cymometer()

        self.timeout = self.TIMEOUT * 10

        try:
            # Note: SDS1104-XE ignores the SP so we gotta do that ourselves.
            self.write(f"waveform_setup SP,0,NP,{count},FP,{first}")
            self.write(f"{trace}:waveform? DAT2")

            response = np.frombuffer(self.port.read_raw(), dtype=np.uint8)
            # Starts with b'DAT2,#9000000000' and ends with b'\n\n'
            points = response[16:-2][0:-1:step]

            timeseries = np.zeros((len(points), 2), dtype=np.float64)

            for n, pt in enumerate(points):
                if pt > 127:
                    pt -= 256

                voltage = pt / _VERT_GRID_LINES * vdiv - voffset
                time = -(tdiv * _HORIZ_GRID_LINES / 2) + (n * step * (1 / sample_rate)) - trigdelay

                timeseries[n] = [time, voltage]

            return Waveform(
                vertical_resolution=256,
                vertical_division=vdiv,
                vertical_offset=voffset,
                vertical_max=(vdiv * _VERT_GRID_LINES / 4) - voffset,
                vertical_min=-(vdiv * _VERT_GRID_LINES / 4) - voffset,
                time_division=tdiv,
                trigger_offset=trigdelay,
                sample_rate=sample_rate,
                sample_step=step,
                frequency=freq,
                data=timeseries
            )

        finally:
            self.timeout = self.TIMEOUT
