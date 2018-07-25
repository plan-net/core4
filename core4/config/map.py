# -*- coding: utf-8 -*-

import collections


class Map(dict):
    """
    a dictionary that supports dot notation
    as well as dictionary access notation

    usage::

      d = DotDict()
      d = DotDict({'val1':'first'})

    set attributes::

      d.val2 = 'second'
      d['val2'] = 'second'

    get attributes::

      d.val2
      d['val2']
    """

    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__

    def __init__(self, dct):
        for key, value in dct.items():
            if isinstance(value, collections.MutableMapping):
                value = Map(value)
            self[key] = value
