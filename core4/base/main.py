"""
This module features :class:`.CoreBase`, the base class to all core4 classes.
All classes inheriting from :class:`.CoreBase` provide the standard features of
core4 classes.
"""

import inspect
import logging
import logging.handlers
import os
import re
import sys
import importlib

import core4.config.main
import core4.config.map
import core4.error
import core4.logger
import core4.logger.filter
import core4.util
from core4.const import CORE4, PREFIX


def is_core4_project(body):
    return re.match(r'.*\_\_project\_\_\s*\=\s*[\"\']{1,3}'
                    + CORE4 + r'[\"\']{1,3}.*', body, re.DOTALL)


class CoreBase:
    """
    This is the base class to all core4 classes. :class:`CoreBase` ships with

    * access to configuration keys/values including project based extra
      configuration settings, use :attr:`.config`
    * standard logging facilities, use :attr:`.logger`
    * a distinct :meth:`.qual_name` based on module path and class name
    * a unique object :meth:`.identifier`, i.e. the job id, the request id or
      the name of the worker
    * helper methods, see :meth:`.progress`

    .. note:: Please note that :class:`.CoreBase` replicates the identifier of
              the class in which scope the object is created. If an object _A_
              derived from  :class:`.CoreBase` has an :attr:`.identifer` not
              ``None`` and creates another object _B_ which inherits from
              :class:`.CoreBase`, too, then the :attr:`.identifier` is passed
              from object _A_ to object _B_.
    """
    # used to hack
    _short_qual_name = None
    _long_qual_name = None
    sys_excepthook = None

    project = None
    identifier = None

    # these config attributes are raised to object level
    upwind = ["log_level"]

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

    @classmethod
    def get_project(cls):
        """
        Identifies the class project.

        :return: project (str)
        """
        modstr = cls.__module__
        project = modstr.split('.')[0]
        module = sys.modules[project]
        # the following is a hack
        if not hasattr(module, "__project__"):
            source = module.__file__
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
                module = importlib.import_module(self.project)
            if hasattr(module, "__project__"):
                if module.__project__ == CORE4:
                    return os.path.join(
                        os.path.dirname(module.__file__),
                        self.project + core4.config.main.CONFIG_EXTENSION)
        return None

    def _make_config(self, *args, **kwargs):
        """
        :return: :class:`.CoreConfig` class to be attached to this class
        """
        return core4.config.main.CoreConfig(*args, **kwargs)

    def _open_config(self):
        # internal method to open and attach core4 cascading configuration
        kwargs = {}
        project_config = self.project_config()
        if project_config and os.path.exists(project_config):
            kwargs["project_config"] = (self.project, project_config)
        kwargs["extra_dict"] = self._build_extra_config()
        self.config = self._make_config(**kwargs)
        pos = self.config._config
        for p in self.qual_name(short=True).split("."):
            pos = pos[p]
        self.class_config = pos
        self._upwind_config()

    def _build_extra_config(self):
        # internal method to create the configuration option reflecting
        # the qual_name
        extra_config = {}
        pos = extra_config
        for p in self.qual_name(short=True).split("."):
            pos[p] = {}
            pos = pos[p]
        for k in self.upwind:
            pos[k] = None
        return extra_config

    def _upwind_config(self):
        for k in self.config.base:
            if k in self.upwind:
                if k in self.class_config:
                    if self.class_config[k] is not None:
                        self.__dict__[k] = self.class_config[k]
                        continue
                    self.__dict__[k] = self.config.base[k]

    def _open_logging(self):
        # internal method to open and attach logging
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
        if CoreBase.sys_excepthook is None:
            CoreBase.sys_excepthook = sys.excepthook
            sys.excepthook = self.excepthook

    def _log_progress(self, p, *args):
        """
        Internal method used to log progress. Overwrite this method to
        implement custom progress logging.

        :param p: current progress value (0.0 - 1.0)
        :param args: message and optional variables using Python format
                     operator
        """
        if args:
            args = list(args)
            fmt = " - {}".format(args.pop(0))
        else:
            fmt = ""
        self.logger.debug('progress at %.0f%%' + fmt, p, *args)

    def progress(self, p, *args, inc=0.05):
        """
        Progress counter calling :meth:`._log_progress` to handle progress and
        message output. All progress outside bins defined by ``inc`` are
        reported only once and otherwise suppressed. This method reliable
        reports progress without creating too much noise in core4 logging
        targets.

        .. note:: Still you can reuse progress reporting. If the current
                  progress is below the last reported progress, then reporting
                  restarts.

        :param p: current progress value (0.0 - 1.0)
        :param args: message and optional variables using Python format
                     operator
        :param inc: progress bins, defaults to 0.05 (5%)
        """
        p_round = round(p / inc) * inc
        if self._progress is None or p_round != self._progress:
            self._log_progress(p_round * 100., *args)
            self._progress = p_round

    @staticmethod
    def format_args(*args, **kwargs):
        """
        format a message given only by args.
        message hast to be the first parameter, formatting second.

        :param args: args
        :return: formatted message.
        """
        if args:
            args = list(args)
            m = args.pop(0)
            if kwargs:
                message = m % kwargs
            elif args:
                message = m % tuple(args)
            else:
                return m
        else:
            message = ""
        return message

    def excepthook(self, *args):
        """
        Internal exception hook to forward unhandled exceptions to core4
        logger with logging level ``CRITICAL``.
        """
        self.logger.critical("unhandled exception", exc_info=args)
        self.sys_excepthook(*args)

    @classmethod
    def module(cls):
        project = ".".join(cls.qual_name().split(".")[:-1])
        if project not in sys.modules:
            return importlib.import_module(project)
        return sys.modules[project]

    @classmethod
    def version(cls):
        project = cls.get_project()
        if project not in sys.modules:
            mod = importlib.import_module(project)
        else:
            mod = sys.modules[project]
        return mod.__version__

    @classmethod
    def pathname(cls):
        return os.path.dirname(cls.module().__file__)

    @classmethod
    def filename(cls):
        return cls.module().__file__
