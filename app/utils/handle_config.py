#!/usr/bin/env python
"""
TODO
"""

from os.path import dirname, join, realpath

from .handle_files import open_json


def get_defaults():
    """
    TODO
    """
    root = join(dirname(realpath(__file__)), "..")
    defaults_file = "config/defaults.json"

    try:
        defaults = open_json(root, defaults_file)
        defaults["paths"]["root"] = root
        for path in ["configs", "results", "assets"]:
            defaults["paths"][path] = join(root, defaults["paths"][path])
        return defaults
    except Exception as e:
        return e


def get_dom_cfg(path: str, file: str):
    """
    TODO
    """
    try:
        return open_json(path, file)
    except Exception as e:
        return e
