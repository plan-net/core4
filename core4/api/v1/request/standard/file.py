import os

from tornado import gen
from tornado.web import StaticFileHandler

from core4.api.v1.request.main import CoreRequestHandler


class FileHandler(CoreRequestHandler, StaticFileHandler):
    """
    The static file handler delivers files based on
    :class:`.CoreRequestHandler` static folder settings and the specified
    core4 default static folder.

    To serve static files, the templates must use the :meth:`.static_url`
    method. If the path starts with a leading slash (``/``), then the method
    translates the static file request into
    ``/core4/api/v1/file/default/<md5_qual_name>/<md5_route>/<path>``. If the
    path does *not* start with a leading slash, then the method translates the
    static file request into
    ``/core4/api/v1/file/project/<md5_qual_name>/<md5_route>/<path>``. Watch
    the ``default`` versus ``project`` modifier in both URLs. All ``project``
    file requests are delivered according to the rendering
    :class:`.CoreRequestHandler` static file settings. All ``default`` file
    requests are delivered according to the global core4 static file settings
    as defined by config attribute ``api.default_static``
    """

    protected = False

    @gen.coroutine
    def get(self, mode, md5_qual_name, md5_route, path, include_body=True):
        (app, container, pattern, cls, *args) = self.application.find_md5(
            md5_qual_name, md5_route)
        if mode == "project":
            self.root = cls.pathname()
        else:
            self.root = self.default_static
        self.request.uri = path
        self.request.path, sep, self.request.query = self.request.uri.partition(
            '?')
        self.absolute_path = os.path.join(self.root, self.request.path)
        self.validate_absolute_path(self.root, self.absolute_path)
        return super().get(path, include_body)
