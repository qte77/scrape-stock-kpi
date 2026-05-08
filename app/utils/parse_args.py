#!/usr/bin/env python
"""Handles arguments to the app"""

from argparse import ArgumentParser
from typing import TypedDict, cast

from ..app import AppModes


class CliArgs(TypedDict):
    """Typed shape of the parsed CLI args returned by `parse_args`."""

    m: str
    provider: str
    headless: bool
    delay: bool


def parse_args() -> CliArgs:
    """Parses and evaluates argv and returns the results."""

    desc = ""

    parser = ArgumentParser(prog="app", description=desc)
    parser.add_argument(
        "-m",
        # "--mode",
        type=str,
        default=AppModes.DEFAULT.value,
        choices=[AppModes.DEFAULT.value, AppModes.TEST.value],
        help="change app mode",
    )
    parser.add_argument(
        "-p",
        "--provider",
        type=str,
        default="",
        help="which provider to test against",
    )
    parser.add_argument(
        "-l", "--headless", action="store_true", help="don't show browser"
    )
    parser.add_argument(
        "-d", "--delay", action="store_true", help="run with random delay"
    )

    return cast(CliArgs, vars(parser.parse_args()))
