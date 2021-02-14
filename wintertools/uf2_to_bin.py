# Copyright (c) 2021 Microsoft Corporation, Alethea Katherine Flowers.
# Adapted from https://github.com/microsoft/uf2/blob/adbb8c7260f938e810eb37f2287f8e1a055ff402/utils/uf2conv.py
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""
Converts uf2 to bin files, used to flash bootloader/circuitpython images using
JLink.
"""

import struct

UF2_MAGIC_START0 = 0x0A324655  # "UF2\n"
UF2_MAGIC_START1 = 0x9E5D5157  # Randomly selected
UF2_MAGIC_END = 0x0AB16F30  # Ditto


def with_file(file, dest=None):
    with open(file, "rb") as fh:
        inputbuf = fh.read()

    outputbuf = with_buf(inputbuf)

    if not dest:
        dest = file + ".bin"

    with open(dest, "wb") as fh:
        fh.write(outputbuf)


def with_buf(buf):
    numblocks = len(buf) // 512
    curraddr = None
    output = b""

    for blockno in range(numblocks):
        ptr = blockno * 512
        block = buf[ptr : ptr + 512]
        header = struct.unpack("<IIIIIIII", block[0:32])

        if header[0] != UF2_MAGIC_START0 or header[1] != UF2_MAGIC_START1:
            print(f"Skipping block at {ptr}; bad magic")
            continue

        if header[2] & 1:
            # NO-flash flag set; skip block
            continue

        datalen = header[4]

        assert datalen <= 476, f"Invalid UF2 data size at {ptr}"

        newaddr = header[3]
        if curraddr is None:
            curraddr = newaddr

        padding = newaddr - curraddr

        assert padding >= 0, f"Block out of order at {ptr}"
        assert padding < 10 * 1024 * 1024, f"More than 10M of padding needed at {ptr}"
        assert padding % 4 == 0, f"Non-word padding size at {ptr}"

        while padding > 0:
            padding -= 4
            output += b"\x00\x00\x00\x00"

        output += block[32 : 32 + datalen]

        curraddr = newaddr + datalen

    return output
