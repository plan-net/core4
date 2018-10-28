from tornado.ioloop import IOLoop

from core4.api.v1.application import CoreApiContainer, serve
from core4.api.v1.request.queue.job import JobHandler
from core4.api.v1.request.queue.state import QueueHandler
from core4.api.v1.request.queue.state import QueueStatus

# sys.queue query object
publisher = QueueStatus()
IOLoop.current().spawn_callback(publisher.update)


class CoreApiServer(CoreApiContainer):
    root = "core4/api/v1"
    rules = [
        (r'/queue', QueueHandler, dict(source=publisher)),
        (r'/job(.*)', JobHandler)
    ]


if __name__ == '__main__':
    serve(CoreApiServer)
