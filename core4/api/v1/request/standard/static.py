#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
core4 :class:`.CoreStaticFileHandler`, based on :mod:`tornado`
:class:`StaticFileHandler <tornado.web.StaticFileHandler>` and
:class:`.CoreBaseHandler`.

"""
import os

import tornado.routing
from tornado.web import StaticFileHandler
from typing import Generator
from core4.api.v1.request.main import CoreBaseHandler

DEFAULT_FILENAME = "index.html"


class CoreStaticFileHandler(CoreBaseHandler, StaticFileHandler):
    """
    A simple handler based on :class:`tornado.web.StaticFileHandler` to serve
    static content from a directory.
    """
    SUPPORTED_METHODS = ("GET", "HEAD", "OPTIONS", "XCARD", "XHELP", "XENTER")
    propagate = ("protected", "title", "author", "tag", "static_path",
                 "icon", "doc", "spa", "default_filename", "subtitle")

    title = "core4 static file handler"
    author = "mra"
    path = None
    default_filename = DEFAULT_FILENAME
    perm_base = "container"

    def __init__(self, *args, **kwargs):
        try:
            self.rsc_id = kwargs.pop("_rsc_id")
        except KeyError:
            self.rsc_id = None
        CoreBaseHandler.__init__(self, *args, **kwargs)
        if "path" not in kwargs:
            kwargs["path"] = self.path
        self._enter = kwargs.pop("enter", None)
        StaticFileHandler.__init__(self, *args, **kwargs)

    def initialize(self, path=None, default_filename=None, *args, **kwargs):
        path = path or self.path or ""
        default_filename = default_filename or self.default_filename
        StaticFileHandler.initialize(self, path, default_filename)
        for attr, value in self.propagate_property(self, kwargs):
            self.__dict__[attr] = value
        if issubclass(self.__class__, CoreStaticFileHandler):
            parent = self.application.container
        else:
            parent = self
        if path.startswith("/"):
            base = parent.project_path()
            path = path[1:]
        else:
            base = parent.pathname()
        self.root = os.path.join(base, path)

    @classmethod
    def get_absolute_path(cls, root, path):
        """Returns the absolute location of ``path`` relative to ``root``.

        ``root`` is the path configured for this `CoreStaticFileHandler`.
        """
        if path is None:
            path = ""
        return super().get_absolute_path(root, path)

    def enter(self, *args, **kwargs):
        """
        On top of the regular ``GET`` method the :class:`CoreStaticFileHandler`
        implements ``POST`` to enter the landing page of the handler. See
        :meth:`.CoreApplication.find_handler`.

        """
        self.logger.debug("redirecting to [%s]", self._enter)
        return self.redirect(self._enter)

    @classmethod
    def get_content(
        cls, abspath: str, start: int = None, end: int = None
    ) -> Generator[bytes, None, None]:
        if abspath != "":
            return StaticFileHandler.get_content(abspath, start, end)
        return


    async def verify_access(self):
        """
        Verifies the user has access to the api container using
        :meth:`User.has_api_access`.

        :return: ``True`` for success, else ``False``
        """
        container = self.application.container.qual_name()
        if self.user and await self.user.has_api_access(container):
            return True
        return False

