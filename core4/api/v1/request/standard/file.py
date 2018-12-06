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
    protected = False

    @gen.coroutine
    def get(self, mode, md5_route, path, include_body=True):
        """
        Retrieve content from default static path (``mode == 'default'``) or
        from the :class:`.CoreRequestHandler` static path
        (``mode == 'project'``).

        Methods:
            GET /file/<mode>/<rule_id>/<path>

        Parameters:
            mode (str): ``default`` to deliver from core4 default static path,
                ``project`` to deliver from request handler static path
            rule_id (str): route ID of the :class:`.CoreRequestHandler`
            path (str): file name relative to the default or project static
                path

        Returns:
            body content

        Raises:
            404: Not Found

        Examples:
            >>> from requests import get
            >>> url = "http://localhost:5001/core4/api/v1"
            >>> get("http://localhost:5001/core4/api/v1/file/default/e9aebdd95287d83f97f14ce07b4852fd/default.css")
            <Response [200]>
        """
        (app, container, pattern, cls, *args) = self.application.find_md5(
            md5_route)
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
