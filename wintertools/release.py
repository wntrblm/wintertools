# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""Helps create releases for Winterbloom stuff"""

import atexit
import collections
import datetime
import importlib.util
import mimetypes
import os
import os.path
import shutil
import subprocess
import tempfile
import webbrowser

import requests

GITHUB_API_TOKEN = os.environ["GITHUB_API_KEY"]

mimetypes.init()


class _Artifacts:
    directory = tempfile.mkdtemp()
    items = []


atexit.register(lambda: shutil.rmtree(_Artifacts.directory, ignore_errors=True))


def _import_config(root):
    config_path = os.path.join(root, ".github", "releasing", "config.py")
    spec = importlib.util.spec_from_file_location("release_config", config_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(*args, capture=True):
    print("$ " + " ".join(args))
    return subprocess.run(
        args, capture_output=capture, encoding="utf-8", check=True
    ).stdout


def _edit_content(editor, content):
    handle, filename = tempfile.mkstemp(".md")
    os.close(handle)

    with open(filename, "w") as fh:
        fh.write(content)

    try:
        run(*(editor + [filename]))

        with open(filename, "r") as fh:
            return fh.read()

    finally:
        os.remove(filename)


def _day_ordinal(day):
    if 4 <= day <= 20 or 24 <= day <= 30:
        return "th"
    else:
        return ["st", "nd", "rd"][day % 10 - 1]


def _git_info() -> dict:
    info = {}

    # Editor
    editor = run("git", "config", "--get", "core.editor").strip().split(" ")
    info["editor"] = editor

    # Root directory

    root = run("git", "rev-parse", "--show-toplevel").strip()

    info["root"] = root

    # Repo name

    origin = run("git", "config", "--get", "remote.origin.url")

    info["repo"] = origin.split(":")[1].rsplit(".")[0]

    # Last release

    run("git", "fetch", "--tags")
    tag_list = run("git", "tag", "--list", "--sort=-creatordate").split("\n")

    info["last_release"] = tag_list[0]

    # List of commits/changes since last version

    changes = run("git", "log", "--format=%s", f"{info['last_release']}..HEAD").split(
        "\n"
    )
    changes = list(filter(None, changes))

    # Arrange changes by category

    categorized_changes = collections.defaultdict(list)

    for change in changes:
        if ": " in change:
            category, change = change.split(": ", 1)
            category = category.capitalize()
        else:
            category = "Other"

        categorized_changes[category].append(change)

    info["changes"] = categorized_changes

    # Generate a new tag name
    now = datetime.datetime.now()

    info["tag"] = now.strftime(f"%Y.%m.{now.day}")
    info["name"] = datetime.datetime.now().strftime(
        f"%B {now.day}{_day_ordinal(now.day)}, %Y"
    )

    return info


def _git_tag(tag_name):
    run("git", "tag", tag_name, capture=False)
    run("git", "push", "origin", tag_name)


def _github_session():
    session = requests.Session()
    session.headers["Accept"] = "application/vnd.github.v3+json"
    session.headers["Authorization"] = f"Bearer {GITHUB_API_TOKEN}"
    return session


def _create_release(session, git_info, description):
    url = f"https://api.github.com/repos/{git_info['repo']}/releases"
    response = session.post(
        url,
        json={
            "tag_name": git_info["tag"],
            "target_commitish": "main",
            "name": git_info["name"],
            "body": description,
            "draft": True,
        },
    )
    response.raise_for_status()
    return response.json()


def _upload_release_artifact(session, release, artifact):
    content_type, _ = mimetypes.guess_type(artifact["path"])

    if not content_type:
        content_type = "application/octet-string"

    with open(artifact["path"], "rb") as fh:
        response = session.post(
            release["upload_url"].split("{", 1)[0],
            params={
                "name": artifact["name"],
            },
            headers={"Content-Type": content_type},
            data=fh.read(),
        )
        response.raise_for_status()


def add_artifact(src, name, **details):
    if not details:
        details = {}

    dst = os.path.join(_Artifacts.directory, name)
    shutil.copy(src, dst)

    details["name"] = name
    details["path"] = dst

    _Artifacts.items.append(details)


def main():
    git_info = _git_info()

    print(f"Working from {git_info['root']}")
    os.chdir(git_info["root"])

    print(f"Tagging {git_info['tag']}...")

    _git_tag(git_info["tag"])

    print("Preparing artifacts...")

    config = _import_config(git_info["root"])
    config.prepare_artifacts(git_info)

    print("Preparing release description...")

    description = config.prepare_description(git_info, _Artifacts.items)
    description = _edit_content(git_info["editor"], description)

    print("Creating release...")
    gh = _github_session()
    release = _create_release(gh, git_info, description)

    for artifact in _Artifacts.items:
        print(f"Uploading {artifact['name']}...")
        _upload_release_artifact(gh, release, artifact)

    webbrowser.open(release["html_url"])


if __name__ == "__main__":
    main()
