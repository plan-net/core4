#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Implements :class:`.CoreSetup` to realise core4 prerequisites, i.e. folders,
default users and roles, and MongoDB collection indices.
"""
import os

import pymongo
import pymongo.errors
from bson.objectid import ObjectId
import core4.util.node
import core4.const
import core4.util.crypt
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
    """

    def make_all(self):
        """
        setup *all* core4 environment prerequisites
        """
        self.make_folder()
        self.make_queue()
        self.make_stdout()
        self.make_role()
        self.make_user()

    @once
    def make_folder(self):
        """
        Creates the core4 folders defined under configuration key ``folder``.
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
    def make_user(self):
        """
        Creates API administration user as defined in core4 configuration
        settings

        * ``api.admin_username``
        * ``api.admin_realname``
        * ``api.admin_password``
        * ``api.contact``

        and a user default role as defined in core4 configuration settings

        * ``api.user_rolename``
        * ``api.user_realname``
        * ``api.user_permission``
        """
        if ((self.config.api.admin_username is None)
                or (self.config.api.admin_password is None)
                or (self.config.api.contact is None)):
            raise TypeError("admin _username, _realname, _password or contact "
                            "not set")
        data = dict(
            name=self.config.api.admin_username,
            realname=self.config.api.admin_realname,
            is_active=True,
            created=core4.util.node.mongo_now(),
            updated=None,
            password=core4.util.crypt.pwd_context.hash(
                self.config.api.admin_password),
            email=self.config.api.contact,
            etag=ObjectId(),
            perm=[core4.const.COP],
        )

        try:
            self.config.sys.role.insert_one(data)
            self.logger.info("created user [%s]",
                             self.config.api.admin_username)
        except pymongo.errors.DuplicateKeyError:
            pass
        try:
            self.config.sys.role.insert_one(dict(
                name=self.config.api.user_rolename,
                realname=self.config.api.user_realname,
                etag=ObjectId(),
                perm=self.config.api.user_permission,
                is_active=True,
                created=core4.util.node.mongo_now(),
                updated=None
            ))
            self.logger.info("created user [%s]",
                             self.config.api.user_rolename)
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

    @once
    def make_role(self):
        """
        Creates collection ``sys.role`` and its index on ``user`` and
        ``email``.
        """
        if "unique_name" not in self.config.sys.role.index_information():
            self.config.sys.role.create_index(
                [
                    ("name", pymongo.ASCENDING)
                ],
                unique=True,
                name="unique_name"
            )
            self.logger.info("created index [unique_name] on [sys.role]")
        if "unique_email" not in self.config.sys.role.index_information():
            self.config.sys.role.create_index(
                [
                    ("email", pymongo.ASCENDING)
                ],
                unique=True,
                name="unique_email",
                partialFilterExpression={"email": {"$exists": True}}
            )
            self.logger.info("created index [unique_email] on [sys.role]")
