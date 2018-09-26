"""
core4.util provides various support and helper methods used by various
core4 packages and modules.
"""

import collections
import getpass
import os
import re

import datetime
import socket
from flask_login import current_user

REGEX_MODIFIER = {
    u'i': re.I,
    u'm': re.M,
    u's': re.S
}


def get_hostname():
    """
    :return: hostname
    """
    return socket.gethostname()


def get_username():
    """
    :return: current login's user name
    """
    if 'SUDO_USER' in os.environ:
        return os.environ['SUDO_USER']
    if current_user and hasattr(current_user, 'username'):
        return current_user.username
    return getpass.getuser()


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


def now():
    """
    :return: current core4 system time (in UTC)
    """
    return datetime.datetime.utcnow()


def get_pid():
    """
    :return: pid of the current process.
    """
    return os.getpid()


class Singleton(type):
    """
    Singleton metaclass, see
    https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python.
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args,
                                                                 **kwargs)
        return cls._instances[cls]
