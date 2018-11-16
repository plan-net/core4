import importlib
import inspect
import io
import os
import pkgutil
import sys
import traceback

import core4.base
import core4.queue.job
import core4.api.v1.application
from core4.util.tool import Singleton

JOB_CLASS = core4.queue.job.CoreJob
API_CONTAINER_CLASS = core4.api.v1.application.CoreApiContainer


class CoreIntrospector(core4.base.CoreBase, metaclass=Singleton):
    """
    The :class:`CoreIntro` class collects information about core4 projects,
    and jobs.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.old_stderr = sys.stderr
        self.old_stdout = sys.stdout
        self._project = []
        self._job = {}
        self._api_container = {}
        self._module = {}
        self._loaded = False

    def _noout(self):
        # internal method to suppress STDOUT and STDERR
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()

    def _onout(self):
        # intenral method to re-open STDOUT and STDERR
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr

    def _flushout(self):
        # internal method to flush STDOUT and STDERR
        sys.stdout.flush()
        sys.stdout.seek(0)
        sys.stderr.seek(0)
        stdout = sys.stdout.read().strip()
        stderr = sys.stderr.read().strip()
        sys.stdout.truncate(0)
        sys.stderr.truncate(0)
        return stdout, stderr

    def iter_project(self):
        self._load()
        return iter(self._project)

    def iter_job(self):
        """
        Iterator through all core4 jobs across projects. The following
        meta information is retrieved:

        * name (see :meth:`.qual_name`)
        * author
        * schedule
        * hidden
        * doc (the ``__doc__`` string of the job class)
        * tag
        * valid (``True`` if job properties and configuration is valid, else
          ``False``)
        * exception with type and traceback in case of errors

        .. note:: Jobs with a ``.hidden`` attribute of ``None`` are not
                  retrieved. All other jobs irrespective of their hidden value
                  (``True`` or ``False``) are enumerated.

        :return: dict generator
        """
        self._load()
        for qual_name, cls in self._job.items():
            try:
                obj = cls()
                if obj.hidden is None:
                    continue  # applies to core4.queue.job.CoreJob
                obj.validate()
                validate = True
                exception = None
                executable = obj.find_executable()
            except Exception as esc:
                validate = False
                exc_info = sys.exc_info()
                exception = {
                    "exception": repr(exc_info[1]),
                    "traceback": traceback.format_exception(*exc_info)
                }
                executable = None
                self.logger.error("cannot instantiate job [%s]",
                                  qual_name, exc_info=exc_info)
            yield {
                "name": qual_name,
                "author": obj.author,
                "schedule": obj.schedule,
                "hidden": obj.hidden,
                "doc": obj.__doc__,
                "tag": obj.tag,
                "valid": validate,
                "exception": exception,
                "python": executable
            }

    def iter_api_container(self):
        self._load()
        for qual_name, cls in self._api_container.items():
            try:
                obj = cls()
                if obj.hidden is None:
                    continue
                exception = None
            except Exception as exc:
                exc_info = sys.exc_info()
                exception = {
                    "exception": repr(exc_info[1]),
                    "traceback": traceback.format_exception(*exc_info)
                }
                self.logger.error("cannot instantiate api container [%s]",
                                  qual_name, exc_info=exc_info)

            for route in cls.rules:
                print(cls().get_alias(), qual_name, route[0], route[1])
                # yield {
                #     "name": qual_name,
                #     "author": obj.author,
                #     "schedule": obj.schedule,
                #     "hidden": obj.hidden,
                #     "doc": obj.__doc__,
                #     "tag": obj.tag,
                #     "valid": validate,
                #     "exception": exception,
                #     "python": executable
                # }

    def _load(self):
        # internal method to collect core4 project packages and iterate
        #   its modules and classes
        if self._loaded:
            return
        self._noout()
        self._project = []
        for pkg in pkgutil.iter_modules():
            if pkg[2]:
                filename = os.path.abspath(
                    os.path.join(pkg[0].path, pkg[1], "__init__.py"))
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
            "collected [%d] projects, [%d] modules and [%d] jobs",
            len(self._project), len(self._module), len(self._job))
        self._loaded = True

    def _load_project(self, pkg):
        # internal method to extract meta information from core4 projects
        record = {
            "name": pkg,
            "version": None,
            "built": None,
            "title": None,
            "description": None,
        }
        module, *_ = self._import_module(pkg)
        if module:
            record.update({
                "version": getattr(module, "__version__", None),
                "built": getattr(module, "__built__", None),
                "title": getattr(module, "title", None),
                "description": getattr(module, "description", None)
            })
        return module, record

    def _iter_module(self, module):
        # internal method to recursively iterate all modules of a core4 project
        for importer, modname, ispkg in pkgutil.iter_modules(
                module.__path__, prefix=module.__name__ + '.'):
            submod, exception, stdout, stderr = self._import_module(modname)
            if submod:
                self._iter_classes(submod)
                if ispkg:
                    self._iter_module(submod)

    def _iter_classes(self, module):
        # internal method to iterate all classes of a module and to extract
        #   the following "special" classes
        #   - core4.queue.job.CoreJob
        members = inspect.getmembers(module, inspect.isclass)
        for (clsname, cls) in members:
            if cls in self._job:
                continue
            for mro in cls.__mro__:
                if mro == JOB_CLASS:
                    self.logger.debug("found job [%s]", cls.qual_name())
                    self._job[cls.qual_name()] = cls
                elif mro == API_CONTAINER_CLASS:
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
