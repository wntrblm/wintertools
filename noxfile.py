# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import nox


@nox.session(reuse_venv=True)
def format(session):
    """Run black code formatter."""
    session.install("black==21.12b0", "isort==5.10.1")
    files = ["wintertools", "noxfile.py"]
    session.run("black", *files)
    session.run("isort", *files)


@nox.session(reuse_venv=True)
def lint(session):
    session.install(
        "flake8==4.0.1", "flake8-bugbear==21.11.29", "flake8-comprehensions==3.7.0"
    )
    files = ["wintertools", "noxfile.py"]
    session.run("flake8", *files)
