import core4.api.v1.request.main
import tornado.web


class DefaultHandler(core4.api.v1.request.main.CoreRequestHandler):

    def initialize(self, *args, status_code=404, **kwargs):
        self.set_status(status_code)

    async def prepare(self):
        await super().prepare()
        raise tornado.web.HTTPError(self._status_code)

    def check_xsrf_cookie(self):
        pass

