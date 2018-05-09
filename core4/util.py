# -*- coding: utf-8 -*-

import re

REGEX_FLAG = {
    u'i': re.I,
    u'm': re.M,
    u's': re.S,
    # u'l': re.L,
    # u'x': re.X,
    # u'u': re.U
}


def parse_regex(regex):
    if not regex.startswith('/'):
        regex = "/" + regex + "/"
    parts = regex.split('/')
    flags = 0
    try:
        pattern = "/".join(parts[1:-1])
        for f in parts[-1].lower():
            flags = flags | REGEX_FLAG[f]
    except:
        raise re.error(
            'invalid regular expression or option [{}]'.format(regex))
    return re.compile(pattern, flags)
