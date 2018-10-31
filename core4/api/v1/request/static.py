from tornado.web import StaticFileHandler

from core4.api.v1.request.main import BaseHandler


class CoreStaticFileHandler(BaseHandler, StaticFileHandler):
    """
    :class:`tornado.web.StaticFileHandler` based on
    :class:`core4.api.v1.main.BaseHandler`.
    """

    def __init__(self, *args, **kwargs):
        BaseHandler.__init__(self)
        StaticFileHandler.__init__(self, *args, **kwargs)

    def verify_access(self):
        """
        There are no additional authorization requirements for static content.

        :return: ``True``
        """
        return True
