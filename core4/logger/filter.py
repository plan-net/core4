# -*- coding: utf-8 -*-

import logging

import core4.util


class CoreLoggingFilter(logging.Filter):

    """
    This filter adds the following properties to class
    :class:`logging.LogRecord`:

    * username
    * hostname
    * identifier
    * qual_name
    """

    def filter(self, record):

        record.username = core4.util.get_username()
        record.hostname = core4.util.get_hostname()
        record.identifier = record.obj.identifier
        record.qual_name = record.obj.qual_name()
        return 1
