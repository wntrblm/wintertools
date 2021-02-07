# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

""" Code that runs on Sol to allow the setup scripts to set voltage outputs for calibration. """

import struct

import usb_midi
import winterbloom_smolmidi as smolmidi
import winterbloom_sol.sol

SYSEX_MARKER = 0x78

outputs = winterbloom_sol.sol.Outputs()
midi_in = smolmidi.MidiIn(usb_midi.ports[0])


while True:
    msg = midi_in.receive()

    if not msg:
        continue

    if msg.type != smolmidi.SYSEX:
        continue

    msg, _ = midi_in.receive_sysex(64)

    if not msg:
        continue

    if msg[0] != SYSEX_MARKER:
        print("Invalid marker")
        continue

    if msg[1] != 0x01:
        print("Invalid command")
        continue

    outputs.led.spin()

    channel = msg[2]

    decoded = bytearray(
        [
            msg[3] << 4 | msg[4],
            msg[5] << 4 | msg[6],
            msg[7] << 4 | msg[8],
            msg[9] << 4 | msg[10],
        ]
    )

    (voltage,) = struct.unpack("f", decoded)

    if channel == 0:
        outputs.cv_a = voltage
    elif channel == 1:
        outputs.cv_b = voltage
    elif channel == 2:
        outputs.cv_c = voltage
    elif channel == 3:
        outputs.cv_d = voltage

    print(voltage)
