# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import itertools
import textwrap

import rich
import rich.console
import rich.padding
import rich.panel
import rich.rule
import rich.text

NON_SEPERATED_NEWLINE = object()


class Printer:
    def __init__(self):
        self._in_list = False

    def _parse(self, x):
        if isinstance(x, str) and (x.startswith("*") or x.startswith("-")):
            x = x.replace("*", " • ", 1)
            x = x.replace("-", " ⁃ ", 1)

            if not self._in_list:
                self._in_list = True
                yield rich.padding.Padding(x, pad=(1, 0, 0, 0))
                return
            else:
                yield x
                return
        elif self._in_list:
            self._in_list = False
            yield NON_SEPERATED_NEWLINE

        if not isinstance(x, str):
            pass

        elif x.startswith("# "):
            x = x.replace("# ", "§ ", 1)
            x = rich.padding.Padding(
                rich.rule.Rule(
                    x,
                    align="left",
                    style="cyan",
                    characters="⋆",
                ),
                pad=(2, 0),
                style="bold cyan",
            )

        elif x.startswith("## "):
            x = x.replace("## ", "⁂ ", 1)
            x = rich.padding.Padding(
                rich.rule.Rule(
                    x,
                    align="left",
                    style="blue",
                    characters="⋅",
                ),
                pad=(1, 0),
                style="bold blue",
            )

        elif x.startswith("!! "):
            x = rich.padding.Padding(
                x.replace("!! ", "[bold yellow blink] ‼ [/] [bold yellow]", 1),
                pad=(1, 0),
            )

        elif x.startswith("> "):
            x = textwrap.indent(x.replace("> ", "", 1), "   ")
            x = "[cyan]»[italic]" + x[1:] + "[/italic]"
            x = rich.padding.Padding(x, pad=(1, 0))

        elif x.startswith("✓ "):
            x = f"[green]{x}[/]"

        yield x

    def __call__(self, *args, **kwargs):
        sep = kwargs.pop("sep", " ")
        parsed = list(itertools.chain(*((self._parse(x) for x in args))))
        args = []

        for n, item in enumerate(parsed):
            if item is NON_SEPERATED_NEWLINE:
                args.append("\n")
            else:
                if n == len(parsed) - 1:
                    args.append(item)
                else:
                    args.extend([item, sep])

        rich.print(*args, sep="", **kwargs)

    def success(self):
        rich.print(
            rich.panel.Panel.fit(
                "[green bold]🎉 Success! 🎉[/]",
                padding=(2, 10),
                style="green",
            )
        )

    def failure(self):
        rich.print(
            rich.panel.Panel.fit(
                "[bold red][blink]💔[/] Oh no, it failed! [blink]💔[/]",
                padding=(2, 5),
                style="red",
            )
        )


print = Printer()


if __name__ == "__main__":
    print("# This is heading 1")
    print("And some regular old text.")
    print("## This is heading 2")
    print("Some more regular text")
    print("!! This is an important notice")
    print("Just some normal text")
    print("* This is a list")
    print("* with two items")
    print("✓ something went well")
    print("- and another list using -")
    print("- weeeee")
    print("Some more normal text")
    print("> this is a blockquote\nwith multiple\nlines")
    print.success()
    print.failure()
