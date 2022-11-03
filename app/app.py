#!/usr/bin/env python
# https://www.diogonunes.com/blog/playwright-cheat-sheet/
# TODO fair value
# page.locator("#fundChart2").click(position={"x":12,"y":107})
"""
TODO mkdir for json if not present, fair value
"""

from enum import Enum
from typing import Union

from .utils.handle_data import shuffle_dict, sort_dict
from .utils.handle_files import save_json
from .utils.handle_playwright import get_values_multiple_url, get_values_single_url

defaults: dict[str, Union[str, int]] = {}
assets: dict[str, dict[str, str]] = {}
config: dict[str, Union[str, dict[str, str]]] = {}


class AppModes(Enum):
    """Provides the states the app can run in"""

    DEFAULT = "prod"
    TEST = "test"


def get_values_wrapper(
    provider: str,
    dom_cfg: dict,
    assets: dict,
    base_url: str,
    save_file: str,
    timeout: int,
    headless: bool = False,
    delay_on: bool = False,
):
    """
    TODO
    """

    results_args = {
        "provider": provider,
        "dom_cfg": dom_cfg,
        "assets": assets,
        "base_url": base_url,
        "timeout": timeout,
        "headless": headless,
        "delay_on": delay_on,
    }

    results = _get_results(**results_args)
    save_json(results, save_file)

    return results


def calculate_averages_wrapper(results: dict, save_file: str):
    """
    TODO
    """
    averages = _calculate_averages(results)
    save_json(averages, save_file)
    return averages


def _calculate_averages(results: dict) -> dict[str, Union[int, str]]:
    """
    TODO
    """

    averages = {}

    for name, scores in results.items():
        scores_valid = [i for i in scores.values() if isinstance(i, int)]
        num_int = len(scores_valid)
        averages[name] = round(sum(scores_valid) / num_int, 2) if num_int > 0 else "N/A"

    return averages


def _get_results(
    provider: str,
    dom_cfg: dict,
    assets: dict,
    base_url: str,
    timeout: int,
    headless: bool = False,
    delay_on: bool = False,
) -> dict[str, dict[str, Union[int, str]]]:
    """
    TODO
    """

    assets = shuffle_dict(assets)
    print(f"shuffled assets: {assets.keys()}")

    get_values_args = {
        "dom_cfg": dom_cfg,
        "assets": assets,
        "base_url": base_url,
        "timeout": timeout,
        "headless": headless,
        "delay_on": delay_on,
    }

    if provider == "portfolio_vis":
        return get_values_single_url(**get_values_args)
    else:
        return sort_dict(get_values_multiple_url(**get_values_args))
