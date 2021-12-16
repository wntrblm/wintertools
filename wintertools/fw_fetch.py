# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""
Helpers that can fetch the latest CircuitPython and uf2 bootloader releases.
"""

import xml.dom.minidom

from rich import print
import requests

from wintertools import fs

BOOTLOADER_RELEASES_URL = (
    "https://api.github.com/repos/adafruit/uf2-samdx1/releases/latest"
)
CIRCUITPYTHON_RELEASES_BASE = "https://adafruit-circuit-python.s3.amazonaws.com/"
CIRCUITPYTHON_RELEASES_URL = "https://adafruit-circuit-python.s3.amazonaws.com/?list-type=2&prefix=bin/{device_name}/en_US/"


def find_latest_bootloader(device_name):
    response = requests.get(BOOTLOADER_RELEASES_URL).json()
    for asset in response["assets"]:
        asset_name = asset["name"]
        if device_name in asset_name and asset_name.endswith(".bin"):
            return asset["browser_download_url"]

    raise RuntimeError(f"Could not find bootloader for {device_name}")


def find_latest_circuitpython(device_name):
    response = requests.get(CIRCUITPYTHON_RELEASES_URL.format(device_name=device_name))
    doc = xml.dom.minidom.parseString(response.text)
    files = doc.getElementsByTagName("Contents")
    files.sort(
        key=lambda tag: tag.getElementsByTagName("LastModified")[
            0
        ].firstChild.nodeValue,
        reverse=True,
    )

    for file in files:
        key = file.getElementsByTagName("Key")[0].firstChild.nodeValue
        release = key.rsplit("en_US")[-1][1:]

        # if a - is in release, it's an alpha/beta/rc/hash build
        if "-" in release:
            continue

        # If it's old, skip it.
        if "OLD" in key:
            continue

        return CIRCUITPYTHON_RELEASES_BASE + key

    raise RuntimeError(f"Could not find CircuitPython release for {device_name}")


def latest_bootloader(device_name):
    bootloader_url = find_latest_bootloader(device_name)
    print(f"Downloading bootloader {bootloader_url}...")
    return fs.download_file_to_cache(bootloader_url, f"bootloader.{device_name}.bin")


def latest_circuitpython(device_name):
    cp_url = find_latest_circuitpython(device_name)
    print(f"Downloading CircuitPython {cp_url}...")
    return fs.download_file_to_cache(cp_url, f"circuitpython.{device_name}.uf2")
