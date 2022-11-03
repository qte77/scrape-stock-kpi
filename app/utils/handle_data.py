#!/usr/usr/bin python
"""
TODO
"""

from random import shuffle


def sort_dict(input: dict):
    """Returns a sorted dict derived from `input`"""
    result = {}
    for key in sorted(input.keys()):
        result[key] = input[key]
    return result


def shuffle_dict(input: dict):
    """Returns a shuffled dict derived from `input`"""
    keys = list(input)
    shuffle(keys)
    return {k: input[k] for k in keys}
