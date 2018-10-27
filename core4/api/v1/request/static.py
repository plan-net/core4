from tornado.web import StaticFileHandler, RequestHandler

from core4.api.v1.request.main import BaseHandler


class CoreStaticFileHandler(BaseHandler, StaticFileHandler):

    def __init__(self, *args, **kwargs):
        BaseHandler.__init__(self)
        StaticFileHandler.__init__(self, *args, **kwargs)

    def verify_access(self):
        return True



class CoreDynamicFileHandler(BaseHandler, RequestHandler):

    def __init__(self, *args, **kwargs):
        BaseHandler.__init__(self)
        StaticFileHandler.__init__(self, *args, **kwargs)

    def verify_access(self):
        return True


