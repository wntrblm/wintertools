# Copyright (c) 2021 Microsoft Corporation, Alethea Katherine Flowers.
# Adapted from https://github.com/microsoft/uf2/blob/adbb8c7260f938e810eb37f2287f8e1a055ff402/utils/uf2conv.py
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""
Converts bin to uf2 files.
"""

import argparse
import pathlib
import struct

UF2_MAGIC_START0 = 0x0A324655  # "UF2\n"
UF2_MAGIC_START1 = 0x9E5D5157  # Randomly selected
UF2_MAGIC_END = 0x0AB16F30  # Ditto

FAMILIES = {
    "SAMD21": 0x68ED2B88,
    "SAML21": 0x1851780A,
    "SAMD51": 0x55114460,
    "NRF52": 0x1B57745F,
    "STM32F1": 0x5EE21072,
    "STM32F4": 0x57755A57,
    "ATMEGA32": 0x16573617,
    "MIMXRT10XX": 0x4FB2D5BD,
}


def with_file(file, start_address, family_id, dest=None):
    with open(file, "rb") as fh:
        inputbuf = fh.read()

    outputbuf = with_buf(inputbuf, start_address=start_address, family_id=family_id)

    if not dest:
        dest = file + ".uf2"

    with open(dest, "wb") as fh:
        fh.write(outputbuf)


def with_buf(input_buf, start_address, family_id):
    datapadding = b""

    while len(datapadding) < 512 - 256 - 32 - 4:
        datapadding += b"\x00\x00\x00\x00"

    numblocks = (len(input_buf) + 255) // 256

    output = b""

    for blockno in range(numblocks):
        ptr = 256 * blockno
        chunk = input_buf[ptr : ptr + 256]
        flags = 0x0

        if family_id:
            flags |= 0x2000

        hd = struct.pack(
            "<IIIIIIII",
            UF2_MAGIC_START0,
            UF2_MAGIC_START1,
            flags,
            ptr + start_address,
            256,
            blockno,
            numblocks,
            family_id,
        )

        while len(chunk) < 256:
            chunk += b"\x00"

        block = hd + chunk + datapadding + struct.pack("<I", UF2_MAGIC_END)

        assert len(block) == 512

        output += block

    return output


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-b",
        "--base",
        type=lambda x: int(x, 0),
        default=0x2000,
        help="The base address of application.",
    )
    parser.add_argument(
        "-f",
        "--family",
        choices=FAMILIES.keys(),
        default="SAMD21",
        help="Set the processor family.",
    )
    parser.add_argument(
        "input",
        type=pathlib.Path,
        help="input file (.bin)",
    )
    parser.add_argument(
        "output",
        type=pathlib.Path,
        help="output destination (.uf2)",
    )

    args = parser.parse_args()

    with_file(args.input, args.base, FAMILIES[args.family], dest=args.output)

    print(f"Created {args.output} for {args.family} @ 0x{args.base:04x}.")


if __name__ == "__main__":
    main()
