# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import os
import tempfile

from wintertools.subprocess import run


def editor():
    return run("git", "config", "--get", "core.editor").strip().split(" ")


def open_editor(content):
    editor_ = editor()

    handle, filename = tempfile.mkstemp(".md")
    os.close(handle)

    with open(filename, "w") as fh:
        fh.write(content)

    try:
        run(*(editor_ + [filename]))

        with open(filename, "r") as fh:
            return fh.read()

    finally:
        os.remove(filename)


def root():
    return run("git", "rev-parse", "--show-toplevel").strip()


def repo_name(remote="origin"):
    origin = run("git", "config", "--get", f"remote.{remote}.url")
    return origin.split(":")[1].rsplit(".")[0]


def fetch_tags():
    run("git", "fetch", "--tags")


def tags():
    return run("git", "tag", "--list", "--sort=-creatordate").split("\n")


def latest_tag():
    return tags()[0]


def get_change_summary(start, end):
    changes = run("git", "log", "--format=%s", f"{start}..{end}").split("\n")
    list(filter(None, changes))
    return changes


def tag(name, push=True):
    run("git", "tag", name, capture=False)

    if push:
        run("git", "push", "origin", name)
