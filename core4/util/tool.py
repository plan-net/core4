#This Source Code Form is subject to the terms of the Mozilla Public
#License, v. 2.0. If a copy of the MPL was not distributed with this
#file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
General helper tools.
"""

import collections


class Singleton(type):
    """
    Singleton metaclass, see
    https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python.
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(
                *args, **kwargs)
        return cls._instances[cls]


class lazyproperty:
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, cls):
        if instance is None:
            return self
        else:
            value = self.func(instance)
            setattr(instance, self.func.__name__, value)
            return value


def dict_merge(dct, merge_dct, add_keys=True):
    """
    Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
    ``dct``.

    This version will return a copy of the dictionary and leave the original
    arguments untouched.

    The optional argument ``add_keys``, determines whether keys which are
    present in ``merge_dict`` but not ``dct`` should be included in the
    new dict.

    :param dct: onto which the merge is executed
    :param merge_dct: dict to be merged into dct
    :param add_keys: whether to add new keys, defaults to ``True``
    :return: updated dict
    """
    dct = dct.copy()
    if not add_keys:
        merge_dct = {
            k: merge_dct[k]
            for k in set(dct).intersection(set(merge_dct))
        }

    for k, v in merge_dct.items():
        if (k in dct and isinstance(dct[k], dict)
                and isinstance(merge_dct[k], collections.Mapping)):
            dct[k] = dict_merge(dct[k], merge_dct[k], add_keys=add_keys)
        else:
            dct[k] = merge_dct[k]

    return dct


def lookahead(iterable_data):
    """
    Pass through all values from the given iterable, augmented by the information
    if there are more values to come after the current one (True),
    or if it is the last value (False).

    :param iterable_data:  iterable type data
    :return: boolean
    """
    iterable = iter(iterable_data)
    last = next(iterable)

    for value in iterable:
        yield last, True
        last = value

    yield last, False
