# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""
Wrapper for talking to the Keithley DMM6500 over VISA

SCPI & Programming reference: https://storage.googleapis.com/files.winterbloom.com/docs/EN-DMM6500-900-01_Users_Manual_DMM6500-900-01A.pdf
"""

import pyvisa.errors
from wintertools import log


class Multimeter:
    RESOURCE_NAME = "USB0::0x05E6::0x6500::04450405::INSTR"
    TIMEOUT = 10 * 1000

    def __init__(self, resource_manager):
        self._connect(resource_manager)

    def _connect(self, resource_manager):
        try:
            resource = resource_manager.open_resource(self.RESOURCE_NAME)
        except pyvisa.errors.VisaIOError as exc:
            log.error("Couldn't connect to multimeter", exc=exc)

        resource.timeout = self.TIMEOUT
        self.port = resource

    def close(self):
        self.port.close()

    def read_voltage(self, average_count=20):
        self.port.write("*RST")
        self.port.write(':SENS:FUNC "VOLT:DC"')
        self.port.write(":SENS:VOLT:RANG 10")
        self.port.write(":SENS:VOLT:INP AUTO")
        self.port.write(":SENS:VOLT:NPLC 1")
        self.port.write(":SENS:VOLT:AZER ON")
        self.port.write(":SENS:VOLT:AVER:TCON REP")
        self.port.write(f":SENS:VOLT:AVER:COUN {average_count}")
        self.port.write(":SENS:VOLT:AVER ON")
        return self.port.query_ascii_values(":READ?")[0]

    def read_voltage_fast(self):
        self.port.write("*RST")
        self.port.write(':SENS:FUNC "VOLT:DC"')
        self.port.write(":SENS:VOLT:RANG 10")
        self.port.write(":SENS:VOLT:INP AUTO")
        self.port.write(":SENS:VOLT:AZER ON")
        return self.port.query_ascii_values(":READ?")[0]
