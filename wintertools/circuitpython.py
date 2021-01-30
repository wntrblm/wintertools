# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""
Helpers for interacting with CircuitPython devices
"""

import time

import serial
import serial.tools.list_ports


def serial_connect(usb_device_id: str):

    port_info = list(serial.tools.list_ports.grep(usb_device_id))[0]
    port = serial.Serial(port_info.device, baudrate=115200, timeout=1)

    return port


def force_into_repl(usb_device_id: str):
    """Forces a circuitpython device into the REPL."""
    port = serial_connect(usb_device_id)

    # Interrupt with Ctrl + C
    port.write(b"\x03")
    # Enter repl with enter after slight delay
    time.sleep(0.2)
    port.write(b"\n")
    port.close()


def reset_via_serial(usb_device_id: str):
    port = serial_connect(usb_device_id)

    # Interrupt with Ctrl + C - not need if already in repl, but doesn't hurt.
    port.write(b"\x03")
    # Enter repl with enter after slight delay
    time.sleep(0.2)
    port.write(b"\n")
    # Reset using Ctrl + D
    port.write(b"\04")
    port.close()
