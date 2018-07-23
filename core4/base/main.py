# -*- coding: utf-8 -*-

"""
This module features CoreBase, the base class to all core4 classes.
"""

import logging
import os
import sys
import re

import core4.config.main
import core4.util
import core4.logger


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
    _qual_name = None
    _identifier = None

    def __init__(self, *args, **kwargs):
        self.account = self.__class__.__module__.split('.')[0]
        # the following is a hack
        if self.account == '__main__':  # pragma: no cover
            dirname = os.path.dirname(sys.argv[0]).split('/')
            pathname = [os.path.splitext(sys.argv[0].split('/')[-1])[0]]
            while dirname:
                init_file = "/".join(dirname + ['__init__.py'])
                pathname.append(dirname.pop(-1))
                if os.path.exists(init_file):
                    body = open(init_file, 'r').read()
                    if re.match(
                            '.*\_\_project\_\_\s*\=\s*[\"\']{}[\"\'].*'.format(
                                CORE4), body, re.DOTALL):
                        self.__class__._qual_name = ".".join(
                            list(reversed(pathname))
                            + [self.__class__.__name__])
                        self.account = pathname.pop(-1)
                        break
        self.section = self.account
        if "bind" in kwargs:
            self.identifier = kwargs["bind"].identifier
        self.config = self._open_config()
        self.logger = self._open_logging()

    def bind(self, obj):
        obj.identifier = self.identifier
        return obj

    def __repr__(self):
        return "{}()".format(self.qual_name())

    @classmethod
    def qual_name(cls, short=True):
        """
        :return: distinct qual_name, the fully qualified module and
                 class name
        """
        if cls._qual_name:  # pragma: no cover (see test_base.test_main)
            return cls._qual_name
        plugin = cls.__module__.split('.')[0]
        if plugin != CORE4 and not short:
            return '.'.join(PLUGIN + [cls.__module__, cls.__name__])
        return '.'.join([cls.__module__, cls.__name__])

    @property
    def identifier(self):
        """
        :return: unique object identifier
        """
        return str(self._identifier or id(self))

    @identifier.setter
    def identifier(self, value):
        self._identifier = value

    def _open_config(self):
        # attach config
        kwargs = {}
        extra_conf = self.account_conf()
        if extra_conf and os.path.exists(extra_conf):
            kwargs["extra_config"] = extra_conf
        return core4.config.CoreConfig(**kwargs)

    def account_conf(self):
        module = sys.modules.get(self.account)
        if module:
            if hasattr(module, "__project__"):
                if module.__project__ == CORE4:
                    return os.path.join(
                        os.path.dirname(module.__file__),
                        self.account + core4.config.main.CONFIG_EXTENSION)
        return None

    def _open_logging(self):
        # attach logging
        self.logger_name = self.qual_name(short=False)
        logger = logging.getLogger(self.logger_name)
        nh = logging.NullHandler()
        logger.addHandler(nh)
        # pass object reference into logging and enable lazy property access
        #   and late binding
        return core4.logger.CoreLoggingAdapter(logger, self)
