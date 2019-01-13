import json
import os

import core4.error
import core4.queue.main
import core4.util.node
from core4.base.main import CoreBase
from core4.const import VENV_PYTHON
from core4.service.introspect import CoreIntrospector
from core4.queue.query import QueryMixin


ITER_COMMAND = """
from core4.service.introspect import CoreIntrospector
print(CoreIntrospector().iter_all())
"""


# todo: requires documentation
# todo: refactor into CoreINtrospector

class CoreProjectInspector(CoreBase, QueryMixin):

    def initialise_object(self):
        self.mongo_url = None
        self.mongo_database = None

    def check_config_files(self):
        self.mongo_url = self.config.mongo_url
        self.mongo_database = self.config.mongo_database
        return {
            "files": list(self.config.__class__._file_cache.keys()),
            "database": self.config.db_info
        }

    def check_mongo_default(self):
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
        folders = {}
        for f in ("transfer", "process", "archive", "temp", "home"):
            folders[f] = self.config.get_folder(f)
        return folders

    def list_project(self):
        home = self.config.folder.home
        if home:
            currpath = os.curdir
            if os.path.exists(home) and os.path.isdir(home):
                queue = core4.queue.main.CoreQueue()
                for project in os.listdir(home):
                    fullpath = os.path.join(home, project)
                    if os.path.isdir(fullpath):
                        pypath = os.path.join(home, project, VENV_PYTHON)
                        os.chdir(fullpath)
                        self.logger.info("listing [%s]", pypath)
                        if os.path.exists(pypath) and os.path.isfile(pypath):
                            # this is Python virtual environment:
                            out = queue.exec_project(project, ITER_COMMAND)
                            yield (project, json.loads(out))
                        else:
                            # no Python virtual environment:
                            yield (project, None)
            os.chdir(currpath)
        else:
            ret = json.loads(CoreIntrospector().iter_all())
            yield (self.project, ret)

    def iter_daemon(self):
        hostname = core4.util.node.get_hostname()
        try:
            return self.get_daemon(hostname)
        except:
            return []

    def summary(self):
        uptime = core4.util.node.uptime()
        return {
            "config": self.check_config_files(),
            "database": self.check_mongo_default(),
            "folder": self.list_folder(),
            "project": dict(self.list_project()),
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
