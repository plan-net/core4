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
    def get(self, path, include_body=True):
        left = os.path.join(self.application.container.root, "file")
        uri_split = self.request.uri[len(left)+1:].split("/")
        rule_name = uri_split[0]
        handler = self.application.container.rule_lookup[rule_name][0]
        self.root = handler.pathname()
        uri = "/".join(uri_split[1:])
        #self.request.uri = os.path.join(left, uri)
        #self.request.path, sep, self.request.query = uri.partition('?')
        path_split = path.split("/")
        super().get("/".join(path_split[1:]), include_body)