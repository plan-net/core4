#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
core4 package, module, project, job and API meta data collector as well as
Python calls in Python environments of different core4 projects.
"""

import importlib
import inspect
import io
import json
import os
import pkgutil
import subprocess
import sys
import traceback

from pip import __version__ as pip_version

import core4.api.v1.application
import core4.base
import core4.queue.job
import core4.queue.query
import core4.service.introspect
import core4.util.node
from core4.const import VENV_PYTHON
from core4.service.introspect.command import ITERATE

try:
    from pip import main as pipmain
except ImportError:
    from pip._internal import main as pipmain

try:
    from pip._internal.operations import freeze
except ImportError:
    from pip.operations import freeze


class CoreIntrospector(core4.base.CoreBase, core4.queue.query.QueryMixin):
    """
    The :class:`CoreIntro` class collects information about
    * core4 projects,
    * core4 jobs,
    * core4 API container,
    * core4 processed configuration files and configuration collection,
    * core4 system folders,
    * alive core4 daemons,
    * Python executable,
    * pip,
    * installed Python packages

    Further this class supports Python calls in project environments sending
    commands from :mod:`core4.service.introspect.command` using
    :func:`exec_project`.
    """

    def initialise_object(self):
        self.old_stderr = sys.stderr
        self.old_stdout = sys.stdout
        self._project = []
        self._job = {}
        self._api_container = {}
        self._module = {}
        self._loaded = False
        self.mongo_url = None
        self.mongo_database = None

    def _noout(self):
        # suppress STDOUT and STDERR
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()

    def _onout(self):
        # re-open STDOUT and STDERR
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr

    def _flushout(self):
        # flush STDOUT and STDERR
        sys.stdout.flush()
        sys.stdout.seek(0)
        sys.stderr.seek(0)
        stdout = sys.stdout.read().strip()
        stderr = sys.stderr.read().strip()
        sys.stdout.truncate(0)
        sys.stderr.truncate(0)
        return stdout, stderr

    def iter_all(self):
        """
        Collects meta information about project, jobs, Python executable,
        pip and installed packages.

        :return: json dump (str)
        """
        container = []
        for c in self.iter_api_container():
            container.append(c)
        ret = json.dumps({
            "project": list(self.iter_project()),
            "job": list(self.iter_job()),
            "container": container,
            "python_version": self.get_python_version(),
            "packages": dict(self.get_packages()),
            "pip": pip_version
        })
        return ret

    def get_packages(self):
        """
        Yields name and version of all installed packages using ``pip freeze``

        :return: generator of (name, version) tuple
        """
        for package in freeze.freeze():
            (name, *version) = package.split("==")
            if version:
                version = version[0]
            yield (name, version or None)

    def get_python_version(self):
        """
        Returns major, minor and patch version of Python executable.

        :return: str of version information
        """
        return "%d.%d.%d" % (
            sys.version_info.major, sys.version_info.minor,
            sys.version_info.micro)

    def iter_project(self):
        """
        Iterator through all core4 projects. The following meta information is
        retrieved:

        * ``built`` - last build date/time
        * ``description`` - from top-level ``__init__.py``  file
        * ``title`` - from top-level ``__init__.py``  file
        * ``version`` - current version

        :return: list of dict generator
        """
        self._load()
        return iter(self._project)

    def iter_job(self):
        """
        Iterator through all core4 jobs across projects. The following
        meta information is retrieved:

        * ``name`` (see :meth:`.qual_name`)
        * ``author``
        * ``schedule``
        * ``hidden``
        * ``doc`` (the ``__doc__`` string of the job class)
        * ``tag``
        * ``valid`` (``True`` if job properties and configuration is valid, else
          ``False``)
        * ``exception`` with type and traceback in case of errors

        .. note:: Jobs with a ``.hidden`` attribute of ``None`` are not
                  retrieved. All other jobs irrespective of their hidden value
                  (``True`` or ``False``) are enumerated.

        :return: list of dict generator
        """
        self._load()
        for qual_name, cls in self._job.items():
            try:
                obj = cls()
                filename = cls.module().__file__
                if obj.hidden is None:
                    continue  # applies to core4.queue.job.CoreJob
                obj.validate()
                validate = True
                exception = None
            except Exception:
                validate = False
                exc_info = sys.exc_info()
                exception = {
                    "exception": repr(exc_info[1]),
                    "traceback": traceback.format_exception(*exc_info)
                }
                self.logger.error("cannot instantiate job [%s]",
                                  qual_name, exc_info=exc_info)
            yield {
                "name": qual_name,
                "source": filename,
                "author": obj.author,
                "schedule": obj.schedule,
                "hidden": obj.hidden,
                "doc": obj.__doc__,
                "tag": obj.tag,
                "valid": validate,
                "exception": exception,
            }

    def iter_api_container(self):
        """
        Iterator through all core4 endpoints across projects. The following
        meta information is retrieved:

        * ``doc`` - handler's doc string
        * ``enabled`` - if ``True`` the project is in scope of
          :meth:`.serve_all`
        * ``exception`` - with type and traceback in case of errors
        * ``name`` - :meth:`.qual_name <core4.base.main.CoreBase.qual_name>`
          of the :class:`.CoreApiContainer`
        * ``rules`` - list of tuples with routing, :class:`.CoreRequestHandler`
          and intialisation arguments

        :return: list of dict generator
        """
        self._load()
        for qual_name, cls in self._api_container.items():
            try:
                if cls == core4.api.v1.application.CoreApiContainer:
                    continue
                obj = cls()
                if not obj.enabled:
                    self.logger.debug("not enabled [%s]", qual_name)
                    continue
                rules = [(r[0], r[1].qual_name()) for r in obj.rules]
                exception = None
            except:
                exc_info = sys.exc_info()
                exception = {
                    "exception": repr(exc_info[1]),
                    "traceback": traceback.format_exception(*exc_info)
                }
                rules = []
                self.logger.error("cannot instantiate api container [%s]",
                                  qual_name, exc_info=exc_info)
            yield {
                "name": qual_name,
                "enabled": obj.enabled,
                "doc": obj.__doc__,
                "exception": exception,
                "rules": rules
            }

    def _load(self):
        # internal method to collect core4 project packages and iterate
        #   its modules and classes
        if self._loaded:
            return
        self._noout()
        self._project = []
        for pkg in pkgutil.iter_modules():
            if pkg[2]:
                self.logger.debug("work [%s]", pkg[1])
                try:
                    filename = os.path.abspath(
                        os.path.join(pkg[0].path, pkg[1], "__init__.py"))
                except:
                    self.logger.warning("silently ignored package [%s]",
                                        pkg[1])
                else:
                    with open(filename, "r", encoding="utf-8") as fh:
                        body = fh.read()
                    if core4.base.main.is_core4_project(body):
                        module, record = self._load_project(pkg[1])
                        self._project.append(record)
                        if module:
                            self._iter_classes(module)
                            self._iter_module(module)
        self._onout()
        self.logger.info(
            "collected [%d] projects, [%d] modules, [%d] jobs, "
            "[%d] api container", len(self._project), len(self._module),
            len(self._job), len(self._api_container))
        self._loaded = True

    def _load_project(self, pkg):
        # internal method to extract meta information from core4 projects
        record = {
            "name": pkg,
            "version": None,
            "built": None,
            "title": None,
            "description": None,
            "filename": None
        }
        module, *_ = self._import_module(pkg)
        if module:
            record.update({
                "version": getattr(module, "__version__", None),
                "built": getattr(module, "__built__", None),
                "title": getattr(module, "title", None),
                "description": getattr(module, "description", None),
                "filename": module.__file__
            })
        return module, record

    def _iter_module(self, module):
        # internal method to recursively iterate all modules of a core4 project
        for importer, modname, ispkg in pkgutil.iter_modules(
                module.__path__, prefix=module.__name__ + '.'):
            try:
                submod, exception, stdout, stderr = self._import_module(
                    modname)
            except:
                raise RuntimeError("with " + modname)
            if submod:
                self._iter_classes(submod)
                if ispkg:
                    self._iter_module(submod)

    def _iter_classes(self, module):
        # internal method to iterate all classes of a module and to extract
        #   the following "special" classes
        #   - core4.queue.job.CoreJob
        #   - core4.api.v1.application.CoreApiContainer
        members = inspect.getmembers(module, inspect.isclass)
        for (clsname, cls) in members:
            if cls in self._job:
                continue
            for mro in cls.__mro__:
                if mro == core4.queue.job.CoreJob:
                    if cls.qual_name() not in self._job:
                        self.logger.debug("found job [%s]", cls.qual_name())
                        self._job[cls.qual_name()] = cls
                elif mro == core4.api.v1.application.CoreApiContainer:
                    if cls != core4.api.v1.application.RootContainer:
                        if cls.qual_name() not in self._api_container:
                            self.logger.debug("found api container [%s]",
                                              cls.qual_name())
                            self._api_container[cls.qual_name()] = cls

    def _import_module(self, name):
        # internal helper method to safely import a core4 module
        exception = mod = None
        try:
            mod = importlib.import_module(name)
        except:
            exc_info = sys.exc_info()
            exception = {
                "exception": repr(exc_info[1]),
                "traceback": traceback.format_exception(*exc_info)
            }
            self.logger.error("encountered error with module [%s]",
                              name, exc_info=exc_info)
        else:
            self.logger.debug("successfully loaded module [%s] at [%s]",
                              name, mod.__file__)
        finally:
            (stdout, stderr) = self._flushout()
        self._module[name] = {
            "module": mod,
            "exception": exception,
            "stdout": stdout,
            "stderr": stderr
        }
        return mod, exception, stdout, stderr

    def check_config_files(self):
        """
        Returns meta information about core4 configuration, i.e. the list of
        processed configuration file and the URL of the core4 ``sys.conf``
        collection if defined.

        :return: dict with keys ``files`` and ``database``
        """
        self.mongo_url = self.config.mongo_url
        self.mongo_database = self.config.mongo_database
        return {
            "files": list(self.config.__class__._file_cache.keys()),
            "database": self.config.db_info
        }

    def check_mongo_default(self):
        """
        Returns MongoDB connection URL if servier state is defined and ``OK``.

        :return: MongoDB connection url (str), ``None`` if not specified or
            error
        """
        try:
            conn = self.config.sys.log.connect()
        except core4.error.Core4ConfigurationError:
            return None
        except:
            raise
        else:
            info = conn.connection.server_info()
            if info["ok"] == 1:
                return "mongodb://" + "/".join(conn.info_url.split("/")[:-1])
            return None

    def list_folder(self):
        """
        Returns meta information about core4 system folders, i.e. ``transfer``,
        ``process``, ``archive``, ``home`` and  ``temp``

        :return: dict of folder (key) locations (value)
        """
        folders = {}
        for f in ("transfer", "process", "archive", "temp", "home"):
            folders[f] = self.config.get_folder(f)
        return folders

    def list_project(self):
        """
        Returns meta information abount installed and accessible core4
        projects. This method uses :meth:`.iter_all` method spawned in core4
        project context to provide details about each project.

        :return: generator of tuple with project name and project meta data
        """
        home = self.config.folder.home
        if home:
            currpath = os.curdir
            if os.path.exists(home) and os.path.isdir(home):
                for project in os.listdir(home):
                    fullpath = os.path.join(home, project)
                    if os.path.isdir(fullpath):
                        pypath = os.path.join(home, project, VENV_PYTHON)
                        os.chdir(fullpath)
                        self.logger.info("listing [%s]", pypath)
                        if os.path.exists(pypath) and os.path.isfile(pypath):
                            # this is Python virtual environment:
                            out = core4.service.introspect.exec_project(
                                project, ITERATE)
                            yield (project, json.loads(out))
                        else:
                            # no Python virtual environment:
                            yield (project, None)
            os.chdir(currpath)
        else:
            ret = json.loads(CoreIntrospector().iter_all())
            yield (self.project, ret)

    def iter_daemon(self):
        """
        Retrieves meta information about active core4 daemons running on this
        node. This method uses method :meth:`.QueryMixin.get_daemon` to query
        daemon meta data.

        * ``_id`` - the identifier of the daemon
        * ``loop`` - the date/time when the daemon entered looping in UTC
        * ``loop_time`` - the timedelta of the daemon looping
        * ``heartbeat`` - the timedelta of the last heartbeat
        * ``kind`` - worker or scheduler

        :return: list of dicts with daemon ``_id``, ``loop`` startup date/time,
            ``loop_time`` interval, last ``heartbeat`` and daemon ``kind``
            (worker, scheduler, app).
        """
        hostname = core4.util.node.get_hostname()
        try:
            return self.get_daemon(hostname)
        except:
            return []

    def summary(self):
        """
        Retrieves core4 setup and configuration summary including

        * Python location and version
        * core4 configuration (see :meth:`.check_config_files`)
        * core4 system database (see :meth:`.check_mongo_default`)
        * core4 system folders (see :meth:`.list_folder`)
        * current user name and groups
        * system uptime
        * core4 alive daemons (see :meth:`.iter_daemon`)

        :return: dict
        """
        uptime = core4.util.node.uptime()
        return {
            "python": {
                "executable": sys.executable,
                "version": tuple(sys.version_info),
            },
            "config": self.check_config_files(),
            "database": self.check_mongo_default(),
            "folder": self.list_folder(),
            "user": {
                "name": core4.util.node.get_username(),
                "group": core4.util.node.get_groups()
            },
            "uptime": {
                "epoch": uptime.total_seconds(),
                "text": "%s" % (uptime)
            },
            "daemon": list(self.iter_daemon())
        }

    def exec_project(self, name, command, wait=True, *args, **kwargs):
        """
        Execute command using the Python interpreter of the project's virtual
        environment.

        :param name: qual_name to extract project name
        :param command: Python commands to be executed
        :param wait: wait and return STDOUT (``True``) or return immediately
                     (defaults to ``False``).
        :param args: to be injected using Python method ``.format``
        :param kwargs: to be injected using Python method ``.format``

        :return: STDOUT if ``wait is True``, else nothing is returned
        """
        project = name.split(".")[0]
        home = self.config.folder.home
        python_path = None
        currdir = os.curdir
        if home is not None:
            python_path = os.path.join(home, project, VENV_PYTHON)
            if not os.path.exists(python_path):
                python_path = None
        if python_path is None:
            self.logger.warning("python not found at [%s], use fallback",
                                python_path)
            python_path = sys.executable
        else:
            self.logger.debug("python found at [%s]", python_path)
            os.chdir(os.path.join(home, project))
        cmd = command.format(*args, **kwargs)
        if wait:
            pipe = subprocess.PIPE
        else:
            pipe = subprocess.DEVNULL
        proc = subprocess.Popen([python_path, "-c", cmd], stdout=pipe,
                                stderr=pipe)
        os.chdir(currdir)
        if wait:
            (stdout, stderr) = proc.communicate()
            out = stdout.decode("utf-8").strip()
            if out == "":
                return "null"
            return out


def exec_project(name, command, wait=True, *args, **kwargs):
    """
    helper method to spawn commands in the context of core4 project
    environment.

    :param name: qual_name to extract project name
    :param command: Python commands to be executed
    :param wait: wait and return STDOUT (``True``) or return immediately
                 (defaults to ``False``).
    :param args: to be injected using Python method ``.format``
    :param kwargs: to be injected using Python method ``.format``

    :return: STDOUT if ``wait is True``, else nothing is returned
    """
    intro = CoreIntrospector()
    return intro.exec_project(name, command, wait, *args, **kwargs)
