"""
core4 :class:`.CoreStaticFileHandler`, based on :mod:`tornado`
:class:`StaticFileHandler <tornado.web.StaticFileHandler>`.

"""
import os
import sys

import magic
from tornado import gen
from tornado.web import HTTPError, StaticFileHandler

from core4.api.v1.request.main import CoreRequestHandler

#: default HTML filename
DEFAULT_FILENAME = "index.html"


class CoreStaticFileHandler(CoreRequestHandler, StaticFileHandler):
    """
    In contrast to torando's :class:`StaticFileHandler` this handler serves
    HTML and asset files from a directory *and* processes variables.

    By default the handler is unprotected. The default HTML file name is
    ``index.html`` (see :attr:`DEFAULT_FILENAME`)
    """

    protected = False
    path = ""

    def __init__(self, *args, **kwargs):
        CoreRequestHandler.__init__(self, *args, **kwargs)
        StaticFileHandler.__init__(self, *args, **kwargs)

    def compute_etag(self):
        """
        Skipps ETag calculation for variables injected files`

        :return: result of inheritied method or None for variables' injected
                 files
        """
        if self.return_etag:
            return super().compute_etag()
        return None

    async def verify_access(self):
        """
        There are no additional authorization requirements for static content.

        :return: ``True``
        """
        return True

    def initialize(self, path=None, default_filename=DEFAULT_FILENAME,
                   inject=None, protected=None):
        """
        Processes all parameters passed in :class:`.CoreApiContainer` ``rules``
        specification.

        :param path: source directory
        :param default_filename: HTML filename, defaults to
                                 :attr:`DEFAULT_FILENAME`
        :param inject: dict of variables inject
        :param protected: requires authenticated users (``True``), defaults to
                          ``False``
        """
        mod_file = sys.modules[self.application.container.__module__].__file__
        mod_dir = os.path.dirname(mod_file)
        if path is None:
            path = self.path
        if not path.startswith(os.sep):
            path = os.path.join(mod_dir, path)
        self.root = os.path.abspath(path)
        if not self.root.endswith(os.path.sep):
            self.root += os.path.sep
        self.default_filename = default_filename
        self.variable = inject
        self.return_etag = False
        self.protected = protected or self.protected

    def head(self, path):
        """
        Process client's ``HEAD`` requiest

        :param path: source file
        :return: result of :meth:`.get` without body
        """
        return self.get(path, include_body=False)

    def get_template_namespace(self):
        """
        Extend :mod:`tornado` namespace with
        :meth:`url <core4.api.v1.application.CoreApiContainer.url`.

        :return: dict with namespace
        """
        namespace = super().get_template_namespace()
        namespace["url"] = self.application.container.url
        return namespace

    def get_variable(self):
        """
        Overwrite this method to inject additional variables to all source
        files.

        :return: empty dict by default
        """
        return {}

    @gen.coroutine
    def get(self, path, include_body=True):
        """
        Determine absolute path and MIME type of source file and use
        :meth:`.render` to inject variables from :meth:`.initialize` and from
        :meth:`.get_variable`.

        :param path: source file
        :param include_body: deliver body, defaults to ``True``
        """
        abspath = os.path.join(self.root, path)
        if abspath.startswith(self.root):
            if os.path.isdir(abspath):
                abspath = os.path.join(abspath, self.default_filename)
            if os.path.exists(abspath):
                self.absolute_path = abspath
                if include_body:
                    mimetype = magic.Magic(mime=True).from_file(abspath)
                    if mimetype == "text/html":
                        variable = self.variable or {}
                        variable.update(self.get_variable())
                        self.render(abspath, **variable)
                    else:
                        self.return_etag = True
                        yield super().get(path, include_body)
                    return
                else:
                    assert self.request.method == "HEAD"
                    return
        raise HTTPError(404, abspath)
