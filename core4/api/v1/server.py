from core4.api.v1.application import CoreApiContainer, serve
from core4.api.v1.request.queue.state import QueueHandler
from core4.api.v1.request.queue.state import publisher
from core4.api.v1.request.queue.state import queue_state


class CoreApiServer(CoreApiContainer):
    root = "core4/api/v1"
    rules = [
        (r'/events', QueueHandler, dict(source=publisher))
    ]


if __name__ == '__main__':
    queue_state.start()
    serve(CoreApiServer)
