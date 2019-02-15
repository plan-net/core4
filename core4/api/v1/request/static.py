#This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
core4 :class:`.CoreStaticFileHandler`, based on :mod:`tornado`
:class:`StaticFileHandler <tornado.web.StaticFileHandler>` and
:class:`.CoreBaseHandler`.

"""
import os

from tornado.web import StaticFileHandler

from core4.api.v1.request.main import CoreBaseHandler, CoreEtagMixin

DEFAULT_FILENAME = "index.html"


class CoreStaticFileHandler(CoreBaseHandler, StaticFileHandler, CoreEtagMixin):
    """
    core4 static file handler extends argument parsing with
    :class:`.CoreApiContainer` and processes the
    """
    SUPPORTED_METHODS = ("GET", "HEAD", "OPTIONS", "XCARD", "XHELP", "XENTER")
    propagate = ("protected", "title", "author", "tag", "static_path",
                 "icon", "default_filename")

    title = "core4 static file handler"
    author = "mra"
    path = None
    default_filename = DEFAULT_FILENAME

    def __init__(self, *args, **kwargs):
        CoreBaseHandler.__init__(self, *args, **kwargs)
        if "path" not in kwargs:
            kwargs["path"] = self.path
        StaticFileHandler.__init__(self, *args, **kwargs)

    def initialize(self, path=None, default_filename=None, *args,
                   **kwargs):
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
        parts = self.request.path.split("/")
        md5_route_id = parts[-1]
        ret = self.application.find_md5(md5_route_id)
        if ret is None:
            return self.redirect("/")
        (app, container, pattern, cls, *args) = ret
        self.logger.info("redirecting to [%s]", pattern)
        return self.redirect(pattern or "/")
