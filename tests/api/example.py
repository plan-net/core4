import datetime
from core4.api.v1.application import CoreApiContainer
from core4.api.v1.tool import serve
from core4.api.v1.request.main import CoreRequestHandler


class ArgTestHandler(CoreRequestHandler):

    def get(self):
        dt = self.get_argument("dt", as_type=datetime.datetime, default=None)
        if dt:
            delta = (datetime.datetime.utcnow() - dt).total_seconds()
        else:
            delta = 0
        self.reply(
            "got: %s (%dsec. to now)" % (dt, delta))

    def post(self):
        self.get()


class CoreApiServer(CoreApiContainer):
    root = "args"
    rules = [
        (r'/test', ArgTestHandler)
    ]


if __name__ == '__main__':
    serve(CoreApiServer)
