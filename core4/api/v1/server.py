from core4.api.v1.application import CoreApiContainer, serve
from core4.api.v1.request.queue.state import QueueHandler
from core4.api.v1.request.queue.state import QueueStatus
from tornado.ioloop import IOLoop

publisher = QueueStatus()
IOLoop.current().spawn_callback(publisher.update)


class CoreApiServer(CoreApiContainer):
    root = "core4/api/v1"
    rules = [
        (r'/events', QueueHandler, dict(source=publisher))
    ]

if __name__ == '__main__':
    serve(CoreApiServer)
