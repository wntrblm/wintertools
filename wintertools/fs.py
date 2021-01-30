# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""
Tools for working with the filesystem, especially copying files and other nonsense like that.
"""

import os.path
import pathlib
import subprocess
import time
import zipfile
import io
import shutil

import requests

import wintertools.platform

CACHE_DIRECTORY = ".cache"


def _find_drive_by_name_macos(name):
    drive = os.path.join(f"/Volumes/{name}")
    if os.path.exists(drive):
        return drive
    raise RuntimeError(f"No drive {name} found, expected at {drive}.")


def find_drive_by_name(name):
    if wintertools.platform.MACOS:
        return _find_drive_by_name_macos(name)
    else:
        raise EnvironmentError("Idk how to find drives on this platform.")


def wait_for_drive(name, timeout=10):
    for n in range(timeout):
        try:
            path = find_drive_by_name(name)
            if n > 1:
                # Wait a second because the drive may not be fully mounted.
                time.sleep(1)
            return path
        except RuntimeError:
            time.sleep(1)
            pass

    raise RuntimeError(f"Drive {path} never showed up.")


def flush(path):
    mountpoint = os.path.join(os.path.join(*os.path.split(path)[:2]))
    fd = os.open(mountpoint, os.O_RDONLY)
    os.fsync(fd)
    os.close(fd)


def unmount(path):
    if wintertools.platform.MACOS:
        disk = None
        mount_output = subprocess.check_output(["mount"]).decode("utf-8").splitlines()

        for line in mount_output:
            items = line.split(" ")
            if items[2] == path:
                disk = items[0].split("/").pop()
                break

        if disk is None:
            print(f"Warning: unable to find device for {path}")
            return

        subprocess.check_output(["diskutil", "unmount", disk])
    else:
        print(f"Idk how to unmount stuff on this OS, so I didn't unmount {path}.")


def copyfile(src, dst):
    # shutil can be a little wonky, so do this manually.
    with open(src, "rb") as fh:
        contents = fh.read()

    with open(dst, "wb") as fh:
        fh.write(contents)
        fh.flush()

    flush(dst)


def deploy_files(srcs_and_dsts, destination):
    os.makedirs(os.path.join(destination, "lib"), exist_ok=True)

    for src, dst in srcs_and_dsts.items():

        full_dst = os.path.join(destination, dst)

        if os.path.isdir(src):
            full_dst = os.path.join(full_dst, os.path.basename(src))
            if os.path.exists(full_dst):
                shutil.rmtree(full_dst)
            shutil.copytree(src, full_dst)

        else:
            if os.path.splitext(full_dst)[1]:
                # Destination is a filename, make sure parent directories exist.
                os.makedirs(os.path.dirname(full_dst), exist_ok=True)
            else:
                # Destination is a directory, make sure it exists.
                os.makedirs(full_dst, exist_ok=True)

            shutil.copy(src, full_dst)

        src = os.path.relpath(src, start=os.path.join(os.curdir, ".."))
        print(f"Copied {src} to {dst}")

    flush(destination)


def clean_pycache(root):
    for p in pathlib.Path(root).rglob("*.py[co]"):
        p.unlink()
    for p in pathlib.Path(root).rglob("__pycache__"):
        p.rmdir()


def cache_path(name):
    return os.path.join(CACHE_DIRECTORY, name)


def download_file_to_cache(url, name):
    os.makedirs(CACHE_DIRECTORY, exist_ok=True)
    dst_path = cache_path(name)

    # ":" Indicates a zip file that needs a single file extracted from it.
    if url.startswith("https+zip://"):
        url, zip_path = url.rsplit(":", 1)
        url = url.replace("https+zip", "https")
    else:
        zip_path = None

    if (
        os.path.exists(dst_path)
        and os.path.getmtime(dst_path) > time.time() - 24 * 60 * 60
    ):
        print(f"Using cached {name}.")
        return dst_path

    response = requests.get(url)

    if zip_path:
        unzip_file(response.content, zip_path, dst_path)
    else:
        with open(dst_path, "wb") as fh:
            fh.write(response.content)

    return dst_path


def download_files_to_cache(urls_and_names):
    for url, name in urls_and_names.items():
        download_file_to_cache(url, name)


def unzip_file(zip_content, zip_path, dst_path):
    zip_data = io.BytesIO(zip_content)

    with zipfile.ZipFile(zip_data, "r") as zipfh:
        file_data = zipfh.read(zip_path)

    with open(dst_path, "wb") as fh:
        fh.write(file_data)


def removeprefix(self: str, prefix: str) -> str:
    if self.startswith(prefix):
        return self[len(prefix) :]
    else:
        return self[:]
