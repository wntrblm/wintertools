# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""
Utilities for interacting with Winterbloom MIDI devices.
"""

import time

import rtmidi.midiutil

from wintertools import teeth

SYSEX_START = 0xF0
SYSEX_END = 0xF7


def wait_for_message(port_in, timeout=1):
    start = time.monotonic()
    while True:
        msg = port_in.get_message()
        if msg:
            msg, _ = msg
            return msg

        if time.monotonic() > start + timeout:
            return None


class MIDIDevice:
    def __init__(self):
        in_port_name = getattr(
            self, "MIDI_PORT_IN_NAME", getattr(self, "MIDI_PORT_NAME", None)
        )
        self.port_in, _ = rtmidi.midiutil.open_midiport(in_port_name, type_="input")
        self.port_in.ignore_types(sysex=False)

        out_port_name = getattr(
            self, "MIDI_PORT_OUT_NAME", getattr(self, "MIDI_PORT_NAME", None)
        )
        self.port_out, _ = rtmidi.midiutil.open_midiport(out_port_name, type_="output")

    def wait_for_message(self):
        return wait_for_message(self.port_in)

    def close(self):
        self.port_in.close_port()
        self.port_out.close_port()

    def sysex(self, command, data=None, response=False, encode=False, decode=False):
        if data is None:
            data = []

        if encode:
            data = teeth.teeth_encode(data)

        self.port_out.send_message(
            [SYSEX_START, self.SYSEX_MARKER, command] + list(data) + [SYSEX_END]
        )

        if response:
            result = self.wait_for_message()

            if decode:
                return teeth.teeth_decode(result[3:-1])

            return result
