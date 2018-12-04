import os
import sys

import magic
from tornado import gen
from tornado.web import HTTPError, StaticFileHandler

from core4.api.v1.request.main import CoreRequestHandler



class FileHandler(CoreRequestHandler, StaticFileHandler):
    """
    In contrast to torando's :class:`StaticFileHandler` this handler serves
    HTML and asset files from a directory *and* processes variables.

    By default the handler is unprotected. The default HTML file name is
    ``index.html`` (see :attr:`DEFAULT_FILENAME`)
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
        self.request.path, sep, self.request.query = self.request.uri.partition('?')
        self.absolute_path = os.path.join(self.root, self.request.path)
        self.validate_absolute_path(self.root, self.absolute_path)
        return super().get(path, include_body)