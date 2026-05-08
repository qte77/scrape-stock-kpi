#!/usr/bin/env python
"""
TODO
"""

from csv import reader, writer
from datetime import datetime
from json import dump, load
from os.path import dirname, join, realpath


def open_json(path: str, name: str) -> dict:
    """
    TODO
    """
    with open(join(path, name)) as lineobj:
        return load(lineobj)


def open_csv_to_dict(path: str, name: str) -> dict:
    """
    TODO
    """
    companies = {}
    with open(join(path, name)) as lineobj:
        csv_reader = reader(lineobj)
        headers = next(csv_reader)
        # TODO refactor repetition into dictcomp?
        for row in csv_reader:
            companies[row[0]] = {
                headers[1]: row[1],
                headers[2]: row[2],
                headers[3]: row[3],
            }
    return companies


def save_json(input: dict, save_file: str) -> None:
    """
    TODO
    """
    with open(save_file, "w") as outfile:
        dump(input, outfile, indent=2)


def save_csv(headers: list[str], rows: list, save_file: str) -> None:
    """
    TODO
    """
    file = join(dirname(realpath(__file__)), save_file)
    with open(file, "w", newline="") as outfile:
        w = writer(outfile)
        w.writerow(headers)
        w.writerows(rows)


def get_save_file_name(provider: str, mode: str, save_path: str, save_filename: str) -> str:
    """
    TODO
    """

    date = datetime.now().strftime("%G-%m-%d_%H-%M")
    name = save_filename.replace("<PROVIDER>", provider)

    return join(save_path, f"{date}_{mode}_{name}")
