import os

import pymongo

from core4.base import CoreBase
from core4.service.introspect import CoreIntrospector
from core4.util import Singleton


def once(f):
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return f(*args, **kwargs)

    wrapper.has_run = False
    return wrapper


class CoreSetup(CoreBase, metaclass=Singleton):

    @once
    def make_folder(self):
        """
        Creates the core4 folders defined with configuration key ``folder``.
        """
        root = self.config.folder.root

        def mkdir(folder):
            path = os.path.join(root, folder)
            if not os.path.exists(path):
                self.logger.warning("created folder [%s]", path)
                os.makedirs(path, exist_ok=True, mode=0o750)

        mkdir(self.config.folder.transfer)
        mkdir(self.config.folder.process)
        mkdir(self.config.folder.archive)
        mkdir(self.config.folder.temp)

    @once
    def make_role(self):
        # todo: requires implementation
        pass

    @once
    def make_queue(self):
        """
        Creates collection ``sys.queue`` and its index on ``name`` and
        ``_hash``. The ``_hash`` attribute ensures that jobs are unique with
        regard to their :meth:`.qual_name` and job arguments.
        """
        self.config.sys.queue.create_index(
            [
                ("name", pymongo.ASCENDING),
                ("_hash", pymongo.ASCENDING)
            ],
            unique=True,
            name="job_args"
        )

    @once
    def make_stdout(self):
        """
        Creates collection ``sys.stdout`` and its TTL index on ``timestamp``.
        """
        ttl = self.config.worker.stdout_ttl
        self.config.sys.stdout.create_index(
            [("timestamp", pymongo.ASCENDING)],
            name="timestamp_ttl",
            expireAfterSeconds=ttl)

    @once
    def register_jobs(self):
        intro = CoreIntrospector()
        lookup = dict([(p["name"], p) for p in intro.iter_project()])
        coll = self.config.sys.project
        for info in intro.iter_job():
            yield info
            # parts = info["name"].split(".")
            # project = parts[0]
            # module = ".".join(parts[0:-1])
            # #print(info["name"], project, module, lookup[project])
