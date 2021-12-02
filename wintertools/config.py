# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import pathlib

import toml
from rich import print, prompt

CONFIG_PATH = pathlib.Path("~/.config/wintertools/config.toml").expanduser()
CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

if not CONFIG_PATH.exists():
    CONFIG = {}
else:
    CONFIG = toml.load(CONFIG_PATH)


def _save_config():
    with CONFIG_PATH.open("w") as fh:
        toml.dump(CONFIG, fh)


def _dict_get_by_dotted_path(dict, path):
    for segment in path.split("."):
        dict = dict[segment]
    return dict


def _dict_set_by_dotted_path(dict, path, value):
    segments = path.split(".")
    path_segments = segments[:-1]
    key = segments[-1]
    for segment in path_segments:
        try:
            dict = dict[segment]
        except KeyError:
            dict[segment] = {}
            dict = dict[segment]

    dict[key] = value


def get(dotted_path, prompt_if_missing=True, default=None):
    try:
        return _dict_get_by_dotted_path(CONFIG, dotted_path)
    except KeyError:
        if default:
            _dict_set_by_dotted_path(CONFIG, dotted_path, default)
            _save_config()
            return default
        elif prompt_if_missing:
            value = prompt.Prompt.ask(
                f"Config {dotted_path} is missing, what should it be?"
            )
            _dict_set_by_dotted_path(CONFIG, dotted_path, value)
            _save_config()
            return value
        else:
            raise


if __name__ == "__main__":
    print(toml.dumps(CONFIG).replace("[", "\\["))
