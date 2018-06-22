# -*- coding: utf-8 -*-

"""
This module features CoreBase, the base class to all core4 classes.
"""

import logging
import os
import sys

import core4.config
import core4.logger
import core4.util


CORE4 = "core4"
PLUGIN = ["core4", "account"]


class CoreBase:
    """
    This is the base class to all core4 classes. :class:`CoreBase` ships with

    * access to configuration sections and options including account based extra
      configuration
    * standard logging batteries included
    * a distinct qual_name based on module path and class name
    * a unique object identifier, i.e. the job id, the request id or the name of
      the worker
    """
    account = None
    section = None

    def __init__(self):
        self.account = self.__class__.__module__.split('.')[0]
        self.section = self.account
        # extra account config
        module = sys.modules.get(self.account)
        kwargs = {}
        if module:
            if hasattr(module, "__project__"):
                if module.__project__ == CORE4:
                    extra_conf = core4.config.main.find_config_file(
                        os.path.dirname(module.__file__),
                        self.account)
                    if extra_conf:
                        kwargs["extra_config"] = extra_conf[0]
        self.config = core4.config.CoreConfig(self.section, **kwargs)
        # attach logging
        self.logger_name = self.qual_name()
        logger = logging.getLogger(self.logger_name)
        nh = logging.NullHandler()
        logger.addHandler(nh)
        self.logger = core4.logger.MongoAdapter(logger, self._extra_log())

    def _extra_log(self):
        return {
            "identifier": self.identifier,
            "hostname": core4.util.get_hostname(),
            "username": core4.util.get_username(),
            "qual_name": self.qual_name(short=True)
        }

    def __repr__(self):
        return "{}()".format(self.qual_name())

    @classmethod
    def qual_name(cls, short=False):
        """
        :return: distinct qual_name, the fully qualified module and
                 class name
        """
        plugin = cls.__module__.split('.')[0]
        if plugin != CORE4 and not short:
            return '.'.join(PLUGIN + [cls.__module__, cls.__name__])
        return '.'.join([cls.__module__, cls.__name__])

    @property
    def identifier(self):
        """
        :return: unique object identifier
        """
        return id(self)
