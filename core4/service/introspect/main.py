#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

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

import core4
import core4.api.v1.application
import core4.base
from core4.base.main import CoreAbstractMixin
import core4.error
import core4.queue.helper.job.base
import core4.queue.job
import core4.queue.helper.job.base
import core4.queue.query
import core4.service.introspect.main
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


class CoreProject(core4.base.CoreBase):
    """
    Collects and provides information about a project.
    """

    def __init__(self, module, capture=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module = module
        self._capture = capture
        self._modules = {}
        self._seen = set()
        self.version = None
        self.built = None
        self.title = None
        self.description = None
        self.filename = None
        self.core4_version = None
        self.core4_build = None
        self.old_stderr = sys.stderr
        self.old_stdout = sys.stdout

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

    def load(self):
        """
        Load information about the project, installed classes (jobs and API
        containers) and modules.
        """
        if self._capture:
            self._noout()
        module, *_ = self._import_module(self.module)
        if module:
            self.version = getattr(module, "__version__", None)
            self.built = getattr(module, "__built__", None)
            self.title = getattr(module, "title", None)
            self.description = getattr(module, "description", None)
            self.filename = module.__file__
            self.core4_version = core4.__version__
            self.core4_build = core4.__built__
            self.logger.debug(
                "loaded core4 package [%s]", self.module)
            self._iter_classes(module)
            self._iter_module(module)
        if self._capture:
            self._onout()
        njob = len(list(self.jobs))
        napi = len(list(self.api_containers))
        self.logger.info("loaded [%s] with [%d] jobs, [%d] api containers",
                         self.module, njob, napi)

    @property
    def jobs(self):
        """
        Retrieves information about implemented :class:`.CoreJob`.
        """
        for cls in self._seen:
            if issubclass(cls, core4.queue.job.CoreJob):
                filename = cls.module().__file__
                qual_name = cls.qual_name()
                try:
                    obj = cls()
                    obj.validate()
                    tag = obj.tag
                    validate = True
                    exception = None
                    schedule = obj.schedule
                except Exception:
                    validate = False
                    tag = None
                    schedule = None
                    exc_info = sys.exc_info()
                    exception = {
                        "exception": repr(exc_info[1]),
                        "traceback": traceback.format_exception(*exc_info)
                    }
                    self.logger.error("cannot instantiate job [%s]",
                                      qual_name, exc_info=exc_info)
                yield {
                    "name": qual_name,
                    "filename": filename,
                    "author": cls.author,
                    "doc": cls.__doc__,
                    "schedule": schedule,
                    "tag": tag,
                    "valid": validate,
                    "exception": exception
                }

    @property
    def api_containers(self):
        """
        Retrieves information about implemented :class:`.CoreApiContainer`.
        """
        for cls in self._seen:
            if issubclass(cls, core4.api.v1.application.CoreApiContainer):
                filename = cls.module().__file__
                qual_name = cls.qual_name()
                try:
                    obj = cls()
                    rules = []
                    for r in obj.iter_rule():
                        rules.append((r.regex.pattern, r.target.qual_name()))
                    exception = None
                    root = cls.root or "/{}".format(cls.get_project())
                except:
                    exc_info = sys.exc_info()
                    exception = {
                        "exception": repr(exc_info[1]),
                        "traceback": traceback.format_exception(*exc_info)
                    }
                    rules = []
                    root = None
                    self.logger.error("cannot instantiate api container [%s]",
                                      qual_name, exc_info=exc_info)
                yield {
                    "name": qual_name,
                    "filename": filename,
                    "doc": cls.__doc__,
                    "rules": rules,
                    "exception": exception,
                    "root": root,
                }

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
            self.logger.debug("successfully imported module [%s] at [%s]",
                              name, mod.__file__)
        finally:
            if self._capture:
                (stdout, stderr) = self._flushout()
            else:
                (stdout, stderr) = None, None
        self._modules[name] = {
            "module": mod,
            "exception": exception,
            "stdout": stdout,
            "stderr": stderr
        }
        return mod, exception, stdout, stderr

    def _iter_classes(self, module):
        # internal method to iterate all classes of a module and to extract
        #   the following "special" classes
        #   - core4.queue.job.CoreJob
        #   - core4.api.v1.application.CoreApiContainer
        members = inspect.getmembers(module, inspect.isclass)
        for (clsname, cls) in members:
            if (issubclass(cls, core4.base.main.CoreBase)
                    and CoreAbstractMixin not in cls.__bases__):
                if cls is core4.queue.job.CoreJob:
                    continue
                if cls is core4.api.v1.application.CoreApiContainer:
                    continue
                if cls in self._seen:
                    continue
                if issubclass(
                        cls, core4.queue.job.CoreJob):
                    self.logger.debug("found job [%s]", cls.qual_name())
                elif issubclass(
                        cls, core4.api.v1.application.CoreApiContainer):
                    self.logger.debug("found api container [%s]",
                                      cls.qual_name())
                self._seen.add(cls)

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


class CoreIntrospector(core4.base.CoreBase, core4.queue.query.QueryMixin):
    """
    Extracts project meta data using :class:`.CoreProject`.
    """

    def initialise_object(self):
        self.project = None

    def run(self, capture=True, dump=False):
        """
        Retrieve the following meta data for the curent virtual environment.

        * ``name`` - of the project
        * ``version`` - latest release number
        * ``build`` - latest build timestamp
        * ``title`` - project title
        * ``description`` - project description
        * ``filename`` - project package filename
        * ``core4_version`` - core4 version
        * ``core4_build`` - core4 build timestamp
        * ``python_version`` - Python version
        * ``packages`` - list of installed packages and version
        * ``pip`` - pip version
        * ``jobs`` - list of implmeneted :class:`.CoreJob` (see below)
        * ``api_containers`` - list of implemented :class:`.CoreApiContainer`
          (see below).

        For jobs the following list of dict is retrieved:

        * ``name`` - ``qual_name``
        * ``filename``
        * ``author``
        * ``doc`` - doc string
        * ``schedule``
        * ``tag``
        * ``valid``
        * ``exception``

        For API containers the following list of dict is retrieved:

        * ``name`` - ``qual_name``
        * ``filename``
        * ``doc`` - doc string
        * ``rules`` - list of :class:`.CoreRequestHandler` and routing pattern
        * ``exception``
        * ``root``

        :param capture: ``True`` to capture and suppress all output to STDOUT
                        and STDERR (defaults to ``True``)
        :param dump: ``True`` to return JSON dump, else Python dict
        :return: list of dict
        """
        # internal method to collect core4 project packages and iterate
        #   its modules and classes
        if self.project is None:
            self.project = []
            for pkg in pkgutil.iter_modules():
                if pkg[2]:
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
                            p = CoreProject(pkg[1], capture=capture)
                            p.load()
                            self.project.append(p)
        data = [
            {
                "name": project.module,
                "version": project.version,
                "build": project.built,
                "title": project.title,
                "description": project.description,
                "filename": project.filename,
                "core4_version": project.core4_version,
                "core4_build": project.core4_build,
                "python_version": self.get_python_version(),
                "packages": dict(self.get_packages()),
                "pip": pip_version,
                "jobs": list(project.jobs),
                "api_containers": list(project.api_containers),
            } for project in self.project
        ]
        if dump:
            js = json.dumps(data)
            return js
        else:
            return data

    def get_home(self):
        """
        Returns the core4 project home path if specified in
        ``config.folder.home`` and exists, else ``None``.
        """
        home = self.config.folder.home
        if home:
            if not (os.path.exists(home) and os.path.isdir(home)):
                raise core4.error.Core4ConfigurationError(
                    "invalid folder.home [{}]".format(home)
                )
        return home

    def introspect(self, project=None):
        """
        Retrieves meta information about the current or all projects. If
        ``config.folder.home`` is specified, then information about all
        installed projects is retrieved using the Python interpreter and
        installed packages of each individual project. If
        ``config.folder.home`` is not specified, then meta data about the
        current project is retrieved.

        :return:
        """
        home = self.get_home()
        if home:
            data = []
            currpath = os.curdir
            for pro in sorted(os.listdir(home)):
                if pro is not None and pro != project:
                    continue
                fullpath = os.path.abspath(os.path.join(home, pro))
                if os.path.isdir(fullpath):
                    pypath = os.path.join(home, pro, VENV_PYTHON)
                    os.chdir(fullpath)
                    self.logger.info("listing [%s]", pypath)
                    if os.path.exists(pypath) and os.path.isfile(pypath):
                        # this is Python virtual environment:
                        out = core4.service.introspect.main.exec_project(
                            pro, ITERATE, comm=True)
                        try:
                            js = json.loads(out)
                            data += js
                        except Exception as exc:
                            self.logger.error("failed to load [%s]:\n%s\n%s",
                                              pro, exc, out)
                    else:
                        self.logger.error("failed to load [%s] due to"
                                          "missing Python virtual "
                                          "environment", pro)
                os.chdir(currpath)
            return data
        else:
            return self.run()

    def retrospect(self):
        """
        Same as :meth:`.introspect` but uses the meta data in collection
        ``sys.job``.

        :return:
        """
        home = self.get_home()
        if home:
            data = {}
            for job in self.config.sys.job.find():
                if "updated_at" in job and job["updated_at"]:
                    if "valid" in job and job["valid"]:
                        if os.path.exists(job["filename"]):
                            data.setdefault(job["project"], [])
                            data[job["project"]].append({
                                "name": job["_id"]
                            })
            return [{"name": p, "jobs": data[p]} for p in data]
        return self.introspect()

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
        return self.get_daemon(hostname=hostname)

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

    def exec_project(self, name, command, wait=True, comm=False, replace=False,
                     *args, **kwargs):
        """
        Execute command using the Python interpreter of the project's virtual
        environment.

        :param name: qual_name to extract project name
        :param command: Python commands to be executed
        :param wait: wait and return STDOUT (``True``) or return immediately
                     (defaults to ``True``).
        :param comm: wait and pass STDOUT (defaults to ``False``).
        :param replace: replace current process (defaults to ``False``).
        :param args: to be injected using Python method ``.format``
        :param kwargs: to be injected using Python method ``.format``

        :return: STDOUT if ``wait is True``, else nothing is returned
        """
        project = name.split(".")[0]
        home = self.get_home()
        python_path = None
        currdir = os.path.abspath(os.curdir)
        if home is not None:
            python_path = os.path.join(home, project, VENV_PYTHON)
            if not os.path.exists(python_path):
                self.logger.warning("python not found at [%s]", python_path)
                python_path = None
        if python_path is None:
            python_path = sys.executable
        self.logger.debug("python found at [%s]", python_path)
        # os.chdir(os.path.join(home, project))
        cmd = command.format(*args, **kwargs)
        if wait:
            if comm:
                stdout = subprocess.PIPE
            else:
                stdout = None
        else:
            stdout = subprocess.DEVNULL
        env = os.environ.copy()
        self.logger.debug("execute with [%s] in [%s]:\n%s", python_path,
                          currdir, cmd)
        if replace:
            os.execve(python_path, [python_path, "-c", cmd], env)
        proc = subprocess.Popen([python_path, "-c", cmd], stdout=stdout,
                                stderr=subprocess.STDOUT, env=env)
        os.chdir(currdir)
        if wait or comm:
            if comm:
                (stdout, stderr) = proc.communicate()
                if stdout:
                    out = stdout.decode("utf-8").strip()
                    if out == "":
                        return "null"
                    return out
                return "null"
            proc.wait()

    def collect_job(self):
        """
        Collects meta data about all known jobs and inserts this information
        into ``sys.job``. The collection's primary use is to store the
        ``created_at`` and general ``__schedule__`` attributes to manage
        scheduling gaps.

        This method is used by :class:`.CoreWorker` and :class:`.CoreScheduler`
        to register existing jobs.

        The following attributes are saved:

        * ``_id`` - the :meth:`.qual_name`
        * ``author`` - of the job
        * ``created_at`` - the date/time when the job has be initially released
        * ``updated_at`` - the date/time when the job has been released lately
        * ``doc`` - the doc string
        * ``exception`` - exception raised with ``traceback``
        * ``filename`` - source of the job
        * ``project`` - name
        * ``schedule`` - in cron format
        * ``tag`` - list of tags
        * ``valid`` - indicates if the job is valid
        """
        self.config.sys.job.update_many(
            filter={},
            update={
                "$set": {
                    "updated_at": None
                },
            }
        )
        now = core4.util.node.mongo_now()
        jobs = {}
        self.logger.info("start registration")
        for project in self.introspect():
            for job in project["jobs"]:
                self.logger.debug("registering job [%s]", job["name"])
                if job["name"] in jobs:
                    self.logger.error("seen [%s]", job["name"])
                update = job.copy()
                del update["name"]
                update["updated_at"] = now
                update["project"] = project["name"]
                self.config.sys.job.update_one(
                    filter={
                        "_id": job["name"]
                    },
                    update={
                        "$set": update,
                        "$setOnInsert": {
                            "created_at": now
                        },
                    },
                    upsert=True
                )
                if job["valid"] and job["schedule"]:
                    doc = self.config.sys.job.find_one(
                        {"_id": job["name"]},
                        projection=["created_at"])
                    jobs[job["name"]] = {
                        "updated_at": now,
                        "schedule": job["schedule"],
                        "created_at": doc["created_at"]
                    }
                    self.logger.info("schedule [%s] at [%s]",
                                     job["name"], job["schedule"])
        self.logger.info("registered [%d] jobs to schedule", len(jobs))
        return jobs


def exec_project(name, command, wait=True, comm=False, replace=False, *args,
                 **kwargs):
    """
    helper method to spawn commands in the context of core4 project
    environment.

    :param name: qual_name to extract project name
    :param command: Python commands to be executed
    :param wait: wait and return STDOUT (``True``) or return immediately
                 (defaults to ``True``).
    :param comm: wait and pass STDOUT (defaults to ``False``).
    :param replace: replace current process (defaults to ``False``).
    :param args: to be injected using Python method ``.format``
    :param kwargs: to be injected using Python method ``.format``
    :return: STDOUT if ``wait is True``, else nothing is returned
    """
    intro = CoreIntrospector()
    return intro.exec_project(name, command, wait, comm, replace, *args,
                              **kwargs)
