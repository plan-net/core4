#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Implements :class:`.ConfigMap`.
"""

import collections.abc

import core4.error


class ConfigMap(dict):
    """
    A read-only dictionary that supports dot notation as well as dictionary
    access notation.
    """

    __getattr__ = dict.__getitem__

    def __init__(self, dct):
        self.__dict__["__ro__"] = False
        for key, value in dct.items():
            if isinstance(value, collections.abc.MutableMapping):
                value = ConfigMap(value)
            self[key] = value
        self.__dict__["__ro__"] = True

    def __setitem__(self, key, value):
        if self.__dict__["__ro__"]:
            raise core4.error.Core4ConfigurationError(
                "core4.config.map.Map is readonly")
        super().__setitem__(key, value)

    def __setattr__(self, key, value):
        raise core4.error.Core4ConfigurationError(
            "core4.config.map.Map is readonly")
