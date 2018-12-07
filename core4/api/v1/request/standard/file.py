import os

from tornado import gen
from tornado.web import StaticFileHandler
from core4.base.main import CoreBase
import core4
import core4.const
from bson.objectid import ObjectId

from core4.api.v1.request.main import CoreRequestHandler


class FileHandler(CoreRequestHandler, StaticFileHandler):
    """
    The static file handler delivers files based on
    :class:`.CoreRequestHandler` static folder settings and the specified
    core4 default static folder.

    To serve static files, the templates must use the :meth:`.static_url`
    method. If the path starts with a leading slash (``/``), then the method
    translates the static file request into
    ``/core4/api/v1/file/default//<md5_route>/<path>``. If the
    path does *not* start with a leading slash, then the method translates the
    static file request into ``/core4/api/v1/file/project/<md5_route>/<path>``.
    Watch the ``default`` versus ``project`` modifier in both URLs. All
    ``project`` file requests are delivered according to the rendering
    :class:`.CoreRequestHandler` static file settings. All ``default`` file
    requests are delivered according to the global core4 static file settings
    as defined by config attribute ``api.default_static``
    """
    author = "mra"
    title = "static file handler for request handler rule ID"

    def __init__(self, *args, **kwargs):
        CoreRequestHandler.__init__(self, *args, **kwargs)
        StaticFileHandler.__init__(self, *args, **kwargs)
        self.default_static = self.config.api.default_static
        if self.default_static and not self.default_static.startswith("/"):
            self.default_static = os.path.join(
                os.path.dirname(core4.__file__), self.default_static)

    async def prepare(self):
        """
        parases the URL and directs the request to the
        :class:`CoreRequestHandler` static folder or the default static folder
        as defined by core4 config ``api.default_static``.
        """
        path = self.request.path[len(core4.const.INFO_URL)+1:]
        (mode, md5_route, *path) = path.split("/")
        (app, container, pattern, cls, *args) = self.application.find_md5(
            md5_route)
        if mode == "project":
            self.root = cls.pathname()
        else:
            self.root = self.default_static
        self.path_args = ["/".join(path)]
        self.identifier = ObjectId()
