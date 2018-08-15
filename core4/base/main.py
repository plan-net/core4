# -*- coding: utf-8 -*-

"""
This module features :class:`.CoreBase`, the base class to all core4 classes.
All classes inheriting from :class:`.CoreBase` provide the developer with the
following features:

* a :meth:`.qual_name` locates the class in the core4 runtime enrivonment. The
  :meth:`.qual_name` for example is used to address jobs, APIs, and widgets
  among others.

* a :attr:`.identifier` identifies the individual object instance of the class;
  this is None with :class:`.CoreBase` and extends into the job ``_id`` or the
  worker identifier for child classes.
"""

import inspect
import logging
import logging.handlers
import os
import re
import sys

import core4.config.main
import core4.logger
import core4.logger.filter
import core4.util

CORE4 = "core4"
PLUGIN = ["core4", "plugin"]


class CoreBase:
    """
    This is the base class to all core4 classes. :class:`CoreBase` ships with

    * access to configuration keys/values including plugin based extra
      configuration settings, use :attr:`.config`, here.
    * standard logging facilities, use :attr:`.logger`, here.
    * a distinct qual_name based on module path and class name with
      :meth:`.qual_name`.
    * a unique object identifier, i.e. the job id, the request id or the name
      of the worker with :attr:`.identifier`.

    .. note:: Please note that :class:`.CoreBase` replicates the identifier of
              the class in which scope the object is created. If an object _A_
              derived from  :class:`.CoreBase` has an :attr:`.identifer` not
              ``None`` and creates another object _B_ which inherits from
              :class:`.CoreBase`, too, then the :attr:`.identifier` is passed
              from object _A_ to object _B_.
    """
    _qual_name = None
    plugin = None
    identifier = None

    def __init__(self):

        # set identifier
        frame = inspect.currentframe().f_back.f_locals
        for n, v in frame.items():
            if hasattr(v, "qual_name"):
                ident = getattr(v, "identifier", None)
                if not isinstance(ident, property):
                    if ident is not None:
                        self.identifier = ident

        self._set_plugin()
        self._open_config()
        self._open_logging()

    def _set_plugin(self):
        self.plugin = self.__class__.__module__.split('.')[0]
        # the following is a hack
        if self.plugin == '__main__':  # pragma: no cover
            dirname = os.path.dirname(sys.argv[0]).split('/')
            pathname = [os.path.splitext(sys.argv[0].split('/')[-1])[0]]
            while dirname:
                init_file = "/".join(dirname + ['__init__.py'])
                pathname.append(dirname.pop(-1))
                if os.path.exists(init_file):
                    body = open(init_file, 'r').read()
                    if re.match(
                            r'.*\_\_project\_\_\s*'
                            r'\=\s*[\"\']{}[\"\'].*'.format(
                                CORE4), body, re.DOTALL):
                        self.__class__._qual_name = ".".join(
                            list(reversed(pathname))
                            + [self.__class__.__name__])
                        self.plugin = pathname.pop(-1)
                        break

    def __repr__(self):
        return "{}()".format(self.qual_name())

    @classmethod
    def qual_name(cls, short=True):
        """
        Returns the distinct ``qual_name``, the fully qualified module and
        class name. With ``short=False`` the prefix ``core4.plugin`` is
        put in front of all plugin classes.

        :param short: defaults to ``False``
        :return: qual_name string
        """
        if cls._qual_name:  # pragma: no cover (see test_base.test_main)
            return cls._qual_name
        plugin = cls.__module__.split('.')[0]
        if plugin != CORE4 and not short:
            return '.'.join(PLUGIN + [cls.__module__, cls.__name__])
        return '.'.join([cls.__module__, cls.__name__])

    def plugin_conf(self):
        """
        Returns the expected path and file name of the plugin configuration.
        Note that this method does not verify that the file actually exists.

        :return: str
        """
        module = sys.modules.get(self.plugin)
        if module:
            if hasattr(module, "__project__"):
                if module.__project__ == CORE4:
                    return os.path.join(
                        os.path.dirname(module.__file__),
                        self.plugin + core4.config.main.CONFIG_EXTENSION)
        return None

    def _open_config(self):
        # internal method to open and attach core4 cascading configuration
        kwargs = {}
        extra_conf = self.plugin_conf()
        if extra_conf and os.path.exists(extra_conf):
            kwargs["extra_config"] = (extra_conf, self.plugin)
        self.config = core4.config.CoreConfig(**kwargs)

    def _open_logging(self):
        # internal method to open and attach core4 logging
        self.logger_name = self.qual_name(short=False)
        logger = logging.getLogger(self.logger_name)
        nh = logging.NullHandler()
        logger.addHandler(nh)
        f = core4.logger.filter.CoreLoggingFilter()
        logger.addFilter(f)
        # pass object reference into logging and enable lazy property access
        #   and late binding
        self.logger = core4.logger.CoreLoggingAdapter(logger, self)
