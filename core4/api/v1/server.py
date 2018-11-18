"""
Delivers the default core4 API server. This server roots to ``/core4/api/v1``
and provides the following endpoints:

* ``/core4/api/v1/login`` - :class:`.LoginHandler` (default handler)
* ``/core4/api/v1/logout`` - :class:`.LogoutHandler` (default handler)
* ``/core4/api/v1/profile`` - :class:`.ProfileHandler` (default handler)
* ``/core4/api/v1/queue`` - :class:`.QueueHandler`
* ``/core4/api/v1/jobs`` - :class:`.JobHandler`
* ``/core4/api/v1/jobs/poll`` - :class:`.JobStream`
* ``/core4/api/v1/enqueue`` - :class:`.JobPost`

Additionally the server creates an endless loop to query collection
``sys.stat`` continuously with :class:`.QueueStatus` to support the
:class:`.QueueHandler`.

Start the server with::

    $ python core4/api/v1/server.py
"""

from tornado.ioloop import IOLoop

from core4.api.v1.application import CoreApiContainer
from core4.api.v1.request.queue.job import JobHandler
from core4.api.v1.request.queue.job import JobPost
from core4.api.v1.request.queue.job import JobStream
from core4.api.v1.request.queue.state import QueueHandler
from core4.api.v1.request.queue.state import QueueStatus
from core4.api.v1.request.role.main import RoleHandler
from core4.api.v1.tool import serve

# sys.stat query object
publisher = QueueStatus()
IOLoop.current().spawn_callback(publisher.update)


class CoreApiServer(CoreApiContainer):
    """
    Default :class:`.CoreApiContainer` serving the standard core4 endpoints
    at ``/core4/api/v1``.
    """
    root = "/core4/api/v1"
    rules = [
        (r'/queue', QueueHandler, dict(source=publisher)),
        (r'/jobs/poll/?(.*)', JobStream),
        (r'/jobs/?(.*)', JobHandler),
        (r'/enqueue', JobPost),
        (r'/roles/?(.*)', RoleHandler),
    ]


if __name__ == '__main__':
    serve(CoreApiServer)
