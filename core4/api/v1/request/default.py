from core4.api.v1.request.main import CoreRequestHandler
import tornado.web


class DefaultHandler(CoreRequestHandler):
    title = "default handler"
    author = "mra"

    """
    Handles all non-existing endpoints throwing ``404`` - ``Not Found`` if the
    user is not logged in, else ``401`` - ``Unauthorized``.
    """

    def initialize(self, *args, status_code=404, **kwargs):
        self.set_status(status_code)

    async def prepare(self):
        await super().prepare()
        self.abort(
            404, "{}://{}{}".format(
                self.request.protocol, self.request.host,
                self.request.path))

    def check_xsrf_cookie(self):
        pass
