# -*- coding: utf-8 -*-

"""
core4.util provides various support and helper methods used by various
core4 packages and modules.
"""

import getpass
import os
import re
import socket
import collections

from flask_login import current_user


REGEX_MODIFIER = {
    u'i': re.I,
    u'm': re.M,
    u's': re.S
}


# def parse_regex(regex):
#     """
#     Translates the passed string into a Python compiled re (regular
#     expression). String format is using the slash delimiter with
#     attached regular expression modifies ``i`` (case-insensitive), ``m``
#     (multi-lines match) and ``s`` (dot matching newlines). A string not
#     following this form is translated into /string/.
#
#     :param regex: regular expression string
#     :return: Python compiled re object
#
#     Raises :class:`re.error` with invalid regular expressions
#     """
#     if not regex.startswith('/'):
#         regex = "/" + regex + "/"
#     parts = regex.split('/')
#     flags = 0
#     try:
#         pattern = "/".join(parts[1:-1])
#         for f in parts[-1].lower():
#             flags = flags | REGEX_MODIFIER[f]
#         return re.compile(pattern, flags)
#     except Exception as exc:
#         raise re.error(
#             "invalid regular expression or option [{}]:\n{}".format(
#                 regex, exc))


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


def dict_merge(dct, merge_dct, add_keys=True, ignore_error=True):
    """ Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
    ``dct``.

    This version will return a copy of the dictionary and leave the original
    arguments untouched.

    The optional argument ``add_keys``, determines whether keys which are
    present in ``merge_dict`` but not ``dct`` should be included in the
    new dict. The optional argument ``ignore_error``, determines whether the
    existence of new keys should raise an exception.

    Args:
        dct (dict) onto which the merge is executed
        merge_dct (dict): dct merged into dct
        add_keys (bool): whether to add new keys

    Returns:
        dict: updated dict
    """
    dct = dct.copy()
    if not add_keys:
        # test = set(merge_dct).difference(set(dct))
        # if (not add_keys) and test:
        #     raise KeyError(
        #         "unknown configuration keys {}".format(test)
        #     )

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

