#!/usr/bin/env python
"""
TODO
"""

from rich.console import Console

from .app import calculate_averages_wrapper, get_values_wrapper
from .utils.handle_assets import get_assets
from .utils.handle_config import get_defaults, get_dom_cfg
from .utils.handle_files import get_save_file_name
from .utils.parse_args import parse_args

if __name__ == "__main__":

    console = Console()

    mode, provider_to_test, headless, delay_on = parse_args().values()
    defaults = get_defaults()
    dom_cfg = get_dom_cfg(defaults["paths"]["configs"], defaults["files"]["config_dom"])
    assets = get_assets(
        defaults["paths"]["assets"],
        defaults["files"]["assets"],
        defaults["files"]["assets_test"],
        mode,
    )

    console.print(f"{mode=}, {headless=}")
    console.print(f"assets={list(assets.keys())}")

    for provider, provider_config in dom_cfg.items():

        if not provider == provider_to_test:
            continue

        console.print(f"Getting values from {provider=}.")

        save_files_kw = {
            "provider": provider,
            "save_path": defaults["paths"]["results"],
            "mode": mode,
        }

        save_scores_file = get_save_file_name(
            save_filename=defaults["files"]["save_scores"], **save_files_kw
        )
        save_avgs_file = get_save_file_name(
            save_filename=defaults["files"]["save_avgs"], **save_files_kw
        )

        get_values_kw = {
            "provider": provider,
            "dom_cfg": provider_config,
            "assets": assets,
            "base_url": defaults["base_urls"][provider],
            "save_file": save_scores_file,
            "timeout": defaults["timeout"],
            "headless": headless,
            "delay_on": delay_on,
        }

        results = get_values_wrapper(**get_values_kw)
        averages = calculate_averages_wrapper(results, save_avgs_file)

        console.print(f"{averages=}")
