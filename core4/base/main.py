#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
This module features :class:`.CoreBase`, the base class to all core4os classes.
All classes inheriting from :class:`.CoreBase` provide the standard features of
core4os classes.
"""

import importlib
import inspect
import logging
import logging.handlers
import os
import re
import sys

import pymongo

import core4.config.main
import core4.const
import core4.logger
import core4.logger.filter
import core4.util.node
from core4.const import CORE4, PREFIX

_except_hook = None


def is_core4_project(body):
    """
    returns ``True`` if the passed string is considered the file content of an
    ``__init__.py`` file of a core4os project.

    core4os projects identify with the following minimal variables::

        __project__ = 'core4'
        __version__ = "1.2.3"
        __built__ = "2019-07-13 10:34:58.963000"
        name = 'foo'
        title = 'bar'
        description = 'foo bar'
    """
    return re.match(r'.*\_\_project\_\_\s*\=\s*[\"\']{1,3}'
                    + CORE4 + r'[\"\']{1,3}.*', body, re.DOTALL)


class CoreBase:
    """
    This is the base class to all core4os classes. :class:`CoreBase` ships with

    * access to configuration keys/values including project based extra
      configuration settings, use ``.config`` propertey to access
      :class:`.CoreConfig`, see documentation of :ref:`config`
    * standard logging facilities, use ``.logger`` property to access
      the logger based on Python standard logging facility, see documentation
      :ref:`logging`
    * a distinct ``qual_name`` based on module path and class name, see method
      :meth:`.qual_name`
    * a unique object ``.identifier``, i.e. the job id, the request id or
      the name of the worker

    .. note:: Please note that :class:`.CoreBase` replicates the identifier of
              the class in which scope the object is created. If an object *A*
              derived from  :class:`.CoreBase` has an ``.identifer`` not
              ``None`` and creates another object *B* which inherits from
              :class:`.CoreBase`, too, then the ``.identifier`` is passed
              from object *A* to object *B*.
    """
    # used to hack
    _short_qual_name = None
    _long_qual_name = None
    sys_excepthook = None

    project = None
    identifier = None

    # these config attributes are raised to object level
    upwind = ["log_level"]
    concurr = False

    _raw_config = None

    def __init__(self):
        # query identifier from instantiating object
        if self.identifier is None:
            identifier = None
            current_frames = inspect.getouterframes(inspect.currentframe())
            for frame_info in current_frames:
                locals = list(frame_info.frame.f_locals.values())
                for v in locals:
                    if issubclass(v.__class__, CoreBase):
                        ident = v.identifier
                        if ident is not None:
                            identifier = ident
                            break
                if identifier is not None:
                    break
            self.identifier = identifier
        self._progress = None
        self.project = self.get_project()
        self._open_config()
        self._open_logging()
        self._event = None
        self.initialise_object()

    def initialise_object(self):
        """
        Called after object instantiation. This method can be overwritten by
        any subclass of :class:`CoreBase` to initialise object variables.
        """
        pass

    @classmethod
    def get_project(cls):
        """
        Identifies the project.

        :return: project (str)
        """
        modstr = cls.__module__
        project = modstr.split('.')[0]
        module = sys.modules[project]
        # the following is a hack
        if not hasattr(module, "__project__"):
            source = os.path.abspath(module.__file__)
        elif project == '__main__':
            source = sys.argv[0]
        else:
            return project
        dirname = os.path.dirname(source).split(os.path.sep)
        pathname = [os.path.splitext(source.split(os.path.sep)[-1])[0]]
        while dirname:
            init_file = os.path.sep.join(dirname + ['__init__.py'])
            pathname.append(dirname.pop(-1))
            if os.path.exists(init_file):
                with open(init_file, 'r') as fh:
                    body = fh.read()
                    if is_core4_project(body):
                        cls._short_qual_name = ".".join(
                            list(reversed(pathname))
                            + [cls.__name__])
                        cls._long_qual_name = ".".join([
                            CORE4, PREFIX, cls._short_qual_name
                        ])
                        project = pathname.pop(-1)
                        break
        return project

    @classmethod
    def project_path(cls):
        """
        Identifies the project path

        :return: str representing  the absolute path name of the project
        """
        project = cls.get_project()
        if project not in sys.modules:
            return importlib.import_module(project)
        return os.path.dirname(sys.modules[project].__file__)

    def __repr__(self):
        """
        :return: str representing the :meth:`.qual_name`
        """
        return "{}()".format(self.qual_name())

    @classmethod
    def qual_name(cls, short=True):
        """
        Returns the distinct ``qual_name``, the fully qualified module and
        class name. With ``short=False`` the prefix ``core4.project`` is put in
        front of all project classes.

        :param short: defaults to ``False``
        :return: qual_name string
        """
        project = cls.get_project()
        if cls._short_qual_name:  # pragma: no cover (see test_base.test_main)
            if short:
                return cls._short_qual_name
            return cls._long_qual_name
        if project != CORE4 and not short:
            return '.'.join([CORE4, PREFIX, cls.__module__, cls.__name__])
        return '.'.join([cls.__module__, cls.__name__])

    def project_config(self):
        """
        Returns the expected path and file name of the project configuration.
        Note that this method does not verify that the file actually exists.

        :return: str
        """
        module = sys.modules.get(self.project)
        if self.project != CORE4:
            if module is None:
                sys.path.append(".")
                module = importlib.import_module(self.project)
            if hasattr(module, "__project__"):
                if module.__project__ == CORE4:
                    return os.path.abspath(
                        os.path.join(
                            os.path.dirname(module.__file__),
                            self.project + core4.config.main.CONFIG_EXTENSION))
        return None

    def _make_config(self, *args, **kwargs):
        # creates the CoreConfig object attached to this class
        return core4.config.main.CoreConfig(*args, **kwargs)

    def _open_config(self):
        # open and attach core4os cascading configuration
        kwargs = {}
        project_config = self.project_config()
        if project_config and os.path.exists(project_config):
            kwargs["project_config"] = (self.project, project_config)
        kwargs["extra_dict"] = self._build_extra_config()
        kwargs["concurr"] = self.concurr
        self.config = self._make_config(**kwargs)
        pos = self.config._config
        for p in self.qual_name(short=True).split("."):
            pos = pos[p]
        self.class_config = pos
        self._upwind_config()

    def _build_extra_config(self):
        # create the configuration option reflecting the qual_name
        extra_config = {}
        pos = extra_config
        for p in self.qual_name(short=True).split("."):
            pos[p] = {}
            pos = pos[p]
        for k in self.upwind:
            pos[k] = None
        return extra_config

    def _upwind_config(self):
        # forward configuration items to object properties as defined by upwind
        for k in self.config.base:
            if k in self.upwind:
                if k in self.class_config:
                    if self.class_config[k] is not None:
                        self.__dict__[k] = self.class_config[k]
                        continue
                    self.__dict__[k] = self.config.base[k]

    def _open_logging(self):
        # open and attach logging
        global _except_hook
        self.logger_name = self.qual_name(short=False)
        logger = logging.getLogger(self.logger_name)
        level = self.log_level
        if level:
            logger.setLevel(getattr(logging, level))
        nh = logging.NullHandler()
        logger.addHandler(nh)
        f = core4.logger.filter.CoreLoggingFilter()
        logger.addFilter(f)
        # pass object reference into logging and enable lazy property access
        #   and late binding
        self.logger = core4.logger.CoreLoggingAdapter(logger, self)
        if _except_hook is None:
            _except_hook = sys.excepthook
            sys.excepthook = self.excepthook

    def progress(self, p, *args, inc=0.05, **kwargs):
        """
        Progress counter to handle progress and message output. All progress
        outside bins defined by ``inc`` are reported only once and otherwise
        suppressed. This method reliable reports progress without creating too
        much noise in core4 logging targets.

        :param p: current progress value (0.0 - 1.0)
        :param args: message and optional variables using Python format
                     operator
        :param inc: progress bins, defaults to 0.05 (5%)
        """
        p_round = round(p / inc) * inc
        if self._progress is None or p_round != self._progress:
            self._progress = p_round
            msg = self.format_args(*args, **kwargs)
            if msg:
                msg = " - " + msg
            self.logger.debug('progress at %.0f%%' + msg, p_round * 100.)

    @staticmethod
    def format_args(*args, **kwargs):
        """
        format a message with Python old style formatting by ``args`` or
        ``kwargs``.

        :return: formatted message.
        """
        if args:
            args = list(args)
            m = args.pop(0)
            if kwargs:
                return m % kwargs
            elif args:
                return m % tuple(args)
            else:
                return m
        return ""

    def excepthook(self, *args):
        """
        Internal exception hook to forward unhandled exceptions to core4os
        logger with logging level ``CRITICAL``.
        """
        self.logger.critical("unhandled exception", exc_info=args)
        _except_hook(*args)

    @classmethod
    def module(cls):
        """
        returns the object's module

        :return: Python module
        """
        project = ".".join(cls.qual_name().split(".")[:-1])
        if project not in sys.modules:
            return importlib.import_module(project)
        return sys.modules[project]

    @classmethod
    def version(cls):
        """
        Returns the project's version.

        :return: str identifying the version
        """
        project = cls.get_project()
        if project not in sys.modules:
            mod = importlib.import_module(project)
        else:
            mod = sys.modules[project]
        return mod.__version__

    @classmethod
    def pathname(cls):
        """
        Returns the pathname of the object's module.

        :return: path name (str)
        """
        return os.path.dirname(cls.module().__file__)

    def trigger(self, name, channel=None, data=None, author=None):
        """
        Triggers an event in collection ``sys.event``.

        This methods uses a special mongo connection with write concern ``0``.
        If the collection ``sys.event`` does not exist, it is created as a
        capped collection with size configured by key ``config.event.size``.

        :param name: of the event
        :param channel: of the event, defaults to channel name ``system``
        :param data: to be attached to the event
        :param author: of the event, defaults to the current username
        :return: event id (MongoDB ``_id``)
        """
        if self._event is None:
            conn = self.config.sys.event.connect(concurr=False)
            if conn:
                wc = self.config.event.write_concern
                conn.with_options(write_concern=pymongo.WriteConcern(w=wc))
                self.logger.debug(
                    "mongodb event setup complete, write concern [%d]", wc)
            else:
                raise core4.error.Core4SetupError("config.event not set")
            existing = conn.connection[
                conn.database].list_collection_names()
            if conn.collection not in existing:
                conn.connection[conn.database].create_collection(
                    name=conn.name,
                    capped=True,
                    size=self.config.event.size
                )
            self._event = conn
        doc = {
            "created": core4.util.node.mongo_now(),
            "name": name,
            "author": author or core4.util.node.get_username(),
            "channel": channel or core4.const.DEFAULT_CHANNEL
        }
        if data:
            doc["data"] = data
        inserted = self._event.insert_one(doc)
        return inserted.inserted_id

    @property
    def raw_config(self):
        """
        raw configuration data access

        :return: :class:`.ConfigMap`
        """
        if self._raw_config is None:
            self._raw_config = self.config._load(False)
        return self._raw_config
