# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""
Wrapper for talking to the Keithley DMM6500 over VISA

SCPI & Programming reference: https://storage.googleapis.com/files.winterbloom.com/docs/EN-DMM6500-900-01_Users_Manual_DMM6500-900-01A.pdf
"""

from . import visa


class Multimeter(visa.Instrument):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_for_voltage_reading = False

    def autozero(self):
        self.write("*RST")
        self.write(':SENS:FUNC "VOLT:DC"')
        self.write(":SENS:AZER:ONCE")

    def read_voltage(self, average_count=20):
        self.write("*RST")
        self.write(':SENS:FUNC "VOLT:DC"')
        self.write(":SENS:VOLT:RANG 10")
        self.write(":SENS:VOLT:INP AUTO")
        self.write(":SENS:VOLT:NPLC 2")
        self.write(":SENS:VOLT:AZER ON")
        self.write(":SENS:VOLT:AVER:TCON REP")
        self.write(f":SENS:VOLT:AVER:COUN {average_count}")
        self.write(":SENS:VOLT:AVER ON")
        return self.port.query_ascii_values(":READ?")[0]

    def setup_voltage_reading(self):
        self.autozero()
        self.write(':SENS:FUNC "VOLT:DC"')
        self.write(":SENS:VOLT:RANG 10")
        self.write(":SENS:VOLT:INP AUTO")
        self.write(":SENS:VOLT:NPLC 1")
        self.write(":SENS:VOLT:AZER ON")
        self._setup_for_voltage_reading = True

    def read_voltage_fast(self):
        if not self._setup_for_voltage_reading:
            self.setup_voltage_reading()
        self.write(':SENS:FUNC "VOLT:DC"')
        self.write(":SENS:VOLT:RANG 10")
        self.write(":SENS:VOLT:INP AUTO")
        self.write(":SENS:VOLT:NPLC 1")
        self.write(":SENS:VOLT:AZER ON")
        values = self.port.query_ascii_values("READ?")
        if len(values) > 1:
            print(values)
        return values[0]
