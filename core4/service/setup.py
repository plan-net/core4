import os

import pymongo
import pymongo.errors

import core4.const
from core4.api.v1.role import Role
from core4.base import CoreBase
from core4.util.tool import Singleton


def once(f):
    """
    Execute decorated methods only once.
    """

    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return f(*args, **kwargs)

    wrapper.has_run = False
    return wrapper


class CoreSetup(CoreBase, metaclass=Singleton):
    """
    Setup core4 environment including

    * folders
    * users and roles
    * collection index of ``sys.queue``
    * collection TTL of ``sys.stdout``
    * collection index of ``sys.stat``
    """

    def make_all(self):
        """
        setup *all* core4 environment prerequisites
        """
        self.make_folder()
        self.make_role()
        self.make_queue()
        self.make_stdout()
        self.make_stat()

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
        """
        Creates API administration user as defined in core4 configuration
        settings

        * ``api.admin_username``
        * ``api.admin_realname``
        * ``api.admin_password``
        * ``api.contact``
        """
        # todo: we might want to add a standard user role with the minimum
        # set of perms required, like /profile
        try:
            Role(
                name=self.config.api.admin_username,
                realname=self.config.api.admin_realname,
                password=self.config.api.admin_password,
                email=self.config.api.contact,
                perm=[core4.const.COP]
            ).save()
        except pymongo.errors.DuplicateKeyError:
            pass

    @once
    def make_queue(self):
        """
        Creates collection ``sys.queue`` and its index on ``name`` and
        ``_hash``. The ``_hash`` attribute ensures that jobs are unique with
        regard to their :meth:`.qual_name` and job arguments.
        """
        if "job_args" not in self.config.sys.queue.index_information():
            self.config.sys.queue.create_index(
                [
                    ("name", pymongo.ASCENDING),
                    ("_hash", pymongo.ASCENDING)
                ],
                unique=True,
                name="job_args"
            )
            self.logger.info("created index [job_args] on [sys.queue]")

    @once
    def make_stat(self):
        """
        Creates collection ``sys.stat`` and its index on ``timestamp``.
        """
        if "timestamp" not in self.config.sys.stat.index_information():
            self.config.sys.stat.create_index(
                [
                    ("timestamp", pymongo.ASCENDING)
                ],
                name="timestamp"
            )
            self.logger.info("created index [timestamp] on [sys.stat]")

    @once
    def make_stdout(self):
        """
        Creates collection ``sys.stdout`` and its TTL index on ``timestamp``.
        If config ``worker.stdout_ttl`` is ``None``, then any existing index
        is removed.
        """
        ttl = self.config.worker.stdout_ttl
        if ttl:
            if "ttl" not in self.config.sys.stdout.index_information():
                self.config.sys.stdout.create_index(
                    [("timestamp", pymongo.ASCENDING)],
                    name="ttl",
                    expireAfterSeconds=ttl)
                self.logger.info("created index [ttl] on [sys.stdout]")
        else:
            if "ttl" in self.config.sys.stdout.index_information():
                self.config.sys.stdout.drop_index(index_or_name="ttl")
                self.logger.warning("removed index [ttl] from [sys.stdout]")
