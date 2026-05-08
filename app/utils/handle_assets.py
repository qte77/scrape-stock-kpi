#!/usr/bin/env python
"""
TODO
"""

from ..app import AppModes
from .handle_files import open_csv_to_dict


def get_assets(
    path: str, file: str, file_test: str, mode: AppModes = AppModes.DEFAULT.value
) -> dict:
    """
    TODO
    """
    assets_file = file if mode == AppModes.DEFAULT.value else file_test
    return open_csv_to_dict(path, assets_file)
