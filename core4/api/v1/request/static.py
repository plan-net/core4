from tornado.web import StaticFileHandler

from tornado.web import HTTPError
import os
from core4.api.v1.request.main import CoreRequestHandler
#from core4.base.main import CoreBase

class CoreStaticFileHandler(CoreRequestHandler):
    """
    :class:`tornado.web.StaticFileHandler` based on
    :class:`core4.api.v1.main.BaseHandler`.
    """

    protected = False
    root = ""

    async def verify_access(self):
        """
        There are no additional authorization requirements for static content.

        :return: ``True``
        """
        return True

    def initialize(self, path=None, default_filename=None):
        self.root = os.path.abspath(path or self.root)
        if not self.root.endswith(os.path.sep):
            self.root += os.path.sep
        self.default_filename = default_filename

    def head(self, path):
        return self.get(path, include_body=False)

    def get(self, path, include_body=True):
        abspath = os.path.join(self.root, path)
        if abspath.startswith(self.root):
            if os.path.exists(abspath):
                if include_body:
                    self.render(abspath)
                    return
                else:
                    assert self.request.method == "HEAD"
        raise HTTPError(404, abspath)
