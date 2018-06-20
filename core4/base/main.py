# -*- coding: utf-8 -*-

"""
This module features CoreBase, the base class to all core4 classes.
"""

import logging
import os
import sys

import core4.config
import core4.logger


class CoreBase:
    """
    This is the base class to all core4 classes. CoreBase ships with

    * access to configuration sections and options
      * account based extra configuration
    * standard logging batteries included
    * a distinct qual_name based on module path and class name
    * a unique object identifier, i.e. job, worker or request id
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
            extra_dir = os.path.dirname(module.__file__)
            extra_conf = os.path.join(extra_dir, self.account + '.yaml')
            kwargs["extra_config"] = core4.config.find_config(extra_conf)
        self.config = core4.config.CoreConfig(self.section, **kwargs)
        # attach logging
        self.logger_name = self.qual_name()
        if not self.logger_name.startswith(core4.logger.CORE4_PREFIX + "."):
            self.logger_name = ".".join([core4.logger.CORE4_PREFIX,
                                         core4.logger.ACCOUNT_PREFIX,
                                         self.qual_name()])
        self.logger = logging.getLogger(self.logger_name)
        nh = logging.NullHandler()
        self.logger.addHandler(nh)

    def __repr__(self):
        return "{}()".format(self.qual_name())

    @classmethod
    def qual_name(cls, short=False):
        """
        :return: distinct qual_name, the fully qualified module and
                 class name
        """
        return '.'.join([cls.__module__, cls.__name__])

    @property
    def identifier(self):
        """
        :return: unique object identifier
        """
        return id(self)
