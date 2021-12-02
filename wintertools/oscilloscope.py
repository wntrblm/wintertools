# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""
Wrapper for talking to the Siglent SDS 1104X-E over VISA.

SCPI & Programming reference: https://storage.googleapis.com/files.winterbloom.com/docs/Programming%20Guide%20PG%2001%20E%2002%20C.pdf
"""

import time

from . import visa


class Oscilloscope(visa.Instrument):
    def __init__(self, resource_manager=None, resource_name=None):
        super.__init__(self, resource_manager, resource_name)
        self._time_div = None

    def connect(self, *args, **kwargs):
        super.connect(*args, **kwargs)
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

    def enable_channel(self, channel: str):
        self.write(f"{channel}:trace on")

    def disable_channel(self, channel: str):
        self.write(f"{channel}:trace off")

    def set_vertical_division(self, channel: str, volts: str):
        self.write(f"{channel}:vdiv {volts}")

    def set_vertical_offset(self, channel: str, volts: str):
        self.write(f"{channel}:ofst {volts}")

    def set_time_division(self, value: str, force: bool = False):
        # Prevent unnecessarily changing the time division, since it can
        # be slow.
        if self._time_div != value or force:
            self.write(f"tdiv {value}")
            self._time_div = value

    def enable_cursors(self):
        self.write("cursor_measure manual")

    def set_cursor_type(self, type: str):
        self.write(f"cursor_type {type}")

    def set_vertical_cursor(self, trace: str, ref: float, dif: float):
        self.write(f"{trace}:cursor_set VREF,{ref},VDIF,{dif}")

    def get_frequency(self):
        return float(self.query("cymometer?"))

    def get_peak_to_peak(self, trace: str):
        try:
            return float(self.query(f"{trace}:parameter_value? PKPK").split(",")[-1])
        except ValueError:
            return 0

    def get_max(self, trace: str):
        try:
            return float(self.query(f"{trace}:parameter_value? MAX").split(",")[-1])
        except ValueError:
            return 0

    def set_trigger_level(self, trig_source: str, trig_level: str):
        self.write(f"{trig_source}:trig_level {trig_level}")

    def show_measurement(self, trace: str, parameter: str):
        self.write(f"parameter_custom {trace},{parameter}")
