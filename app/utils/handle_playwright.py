#!/usr/bin/env python
"""
TODO
"""

from math import ceil
from random import randrange
from re import IGNORECASE, UNICODE, compile
from time import perf_counter, sleep
from typing import Any

from playwright.sync_api import expect, sync_playwright
from rich.console import Console
from rich.table import Table
from tqdm import tqdm


def get_values_multiple_url(
    dom_cfg: dict,
    assets: dict,
    base_url: str,
    timeout: int,
    headless: bool = False,
    delay_on: bool = False,
):
    """
    TODO
    """

    clear_cols = 20
    console = Console()
    results = {}
    summary = {}

    table = Table(show_header=True)
    table.add_column("Company", width=clear_cols)
    if delay_on:
        table.add_column("Delay", width=10)
    table.add_column("Elapsed", width=10)

    for asset_name, asset_values in tqdm(
        assets.items(), " " * clear_cols, position=0, leave=True
    ):

        elapsed_time = []

        assset_len = len(asset_name)
        if assset_len >= clear_cols:
            asset_disp = asset_name[: (clear_cols - 1)]
        else:
            cols_to_clear = " " * (clear_cols - assset_len)
            asset_disp = f"{asset_name}{cols_to_clear}"

        print(f"\r{asset_disp}", end="")

        if delay_on:
            start = perf_counter()
            delay = randrange(0, 3) if randrange(0, 99) < 90 else randrange(5, 9)
            for i in range(delay, 0, -1):
                sleep(1)
            end = perf_counter()
            elapsed_time.append(f"{(end-start):0.2f}")

        start = perf_counter()
        url = _get_url(base_url, asset_values)
        results[asset_name] = _get_result(asset_name, url, dom_cfg, timeout, headless)
        end = perf_counter()
        elapsed_time.append(f"{(end-start):0.2f}")

        summary[asset_name] = elapsed_time

    for company, elapsed in summary.items():
        if delay_on:
            table.add_row(company, elapsed[0], elapsed[1])
        else:
            table.add_row(company, elapsed[0])

    console.print(table)

    return results


def get_values_single_url(
    dom_cfg: dict,
    assets: dict,
    base_url: str,
    timeout: int,
    headless: bool = False,
    delay_on: bool = False,
):
    """ "
    TODO
    """

    # TODO refactor
    k = 0
    max_symbols = 25
    symbols = ""

    len_symbols = ceil(len(assets) / max_symbols)
    results = [None] * len_symbols

    for i, items in enumerate(assets.values()):
        symbol = items["symbol"]
        symbols = f"{symbols}&symbol{i}={symbol}"
        if not i == 0 and (i % max_symbols) == 0:
            url = f"{base_url}{symbols}"
            results[k] = _get_result(
                "Portfolio Optimization", url, dom_cfg, headless, timeout
            )

    return results


def _get_page(
    pw_context,
    # title: str,
    url: str,
    cookie_selector: str,
    cookie_frame: str,
    timeout: int,
    headless: bool = False,
):
    """
    TODO
    """

    try:
        browser = pw_context.chromium.launch(headless=headless)  # , slow_mo=50)
        page = browser.new_page()
        _ = page.goto(url)
        # TODO provider frequently change the company name
        # expect(page).to_have_title(
        #     compile(title, flags=IGNORECASE | UNICODE), timeout=timeout
        # )
        _handle_page_cookies(page, cookie_selector, cookie_frame, timeout)
        return page
    except Exception as e:
        print(f"get page {e=}")
        return str(e)


def _handle_page_cookies(
    page, cookie_selector: str, cookie_frame: str = None, timeout: int = None
) -> None:
    """
    TODO
    """

    if cookie_frame is None or cookie_frame == "":
        page.locator(cookie_selector).click()
    else:
        try:
            page.wait_for_selector(cookie_frame).content_frame()
            page.frame_locator(cookie_frame).locator(cookie_selector).click()
            # page.wait_for_url(url)
        except Exception as e:
            print(f"cookie {e=}")


def _get_url(base_url: str, asset_values: dict):
    """
    TODO
    """

    url = base_url

    for k, v in asset_values.items():
        if not k == "symbol":
            url = url.replace(f"<{k}>".upper(), v)

    return url


def _get_scores_from_page(dom_cfg: dict, page: Any, timeout: int):
    """
    TODO
    """

    scores = {}
    has_class = dom_cfg["dom_has"]["has_class"]

    for k, v in dom_cfg["dom_selectors"].items():

        click = v["click"]
        selector = v["selector"]

        try:
            if click:
                page.locator(click).click()
            scores[k] = int(
                page.inner_text(f"{selector} >> {has_class}", timeout=timeout)
            )
        except Exception as e:
            scores[k] = str(e)

    return scores


def _get_result(
    asset_name: str, url: str, dom_cfg: dict, timeout: int, headless: bool = False
):
    """
    TODO
    """

    with sync_playwright() as pw_context:

        page_kw = {
            "pw_context": pw_context,
            "title": asset_name,
            "url": url,
            "cookie_selector": dom_cfg["dom_selector_cookies"],
            "cookie_frame": dom_cfg["dom_selector_cookies_frame"],
            "headless": headless,
            "timeout": timeout,
        }

        try:
            page = _get_page(**page_kw)
        except Exception as e:
            print(f"page {e=}")
            return {"exception": str(e)}

        try:
            return _get_scores_from_page(dom_cfg=dom_cfg, page=page, timeout=timeout)
        except Exception as e:
            print(f"results {e=}")
            return {"exception": str(e)}
