# -*- coding: utf-8 -*-

import collections

import core4.error


class Map(dict):
    """
    A dictionary that supports dot notation as well as dictionary access
    notation.
    """

    __getattr__ = dict.__getitem__

    def __init__(self, dct):
        self.__dict__["__ro__"] = False
        for key, value in dct.items():
            if isinstance(value, collections.MutableMapping):
                value = Map(value)
            self[key] = value
        self.__dict__["__ro__"] = True

    def __setitem__(self, key, value):
        if self.__dict__["__ro__"]:
            raise core4.error.Core4ConfigurationError("core4.config.map.Map "
                                                      "is readonly")
        super().__setitem__(key, value)

    def __setattr__(self, key, value):
        raise core4.error.Core4ConfigurationError("core4.config.map.Map "
                                                  "is readonly")
