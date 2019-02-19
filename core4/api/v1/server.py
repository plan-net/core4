# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Delivers the default core4 API server. This server roots to ``/coco/v1``
and provides the following endpoints:

* ``/coco/v1/login`` - :class:`.LoginHandler` (default handler)
* ``/coco/v1/logout`` - :class:`.LogoutHandler` (default handler)
* ``/coco/v1/profile`` - :class:`.ProfileHandler` (default handler)
* ``/coco/v1/queue`` - :class:`.QueueHandler`
* ``/coco/v1/jobs`` - :class:`.JobHandler`
* ``/coco/v1/jobs/poll`` - :class:`.JobStream`
* ``/coco/v1/enqueue`` - :class:`.JobPost`
* ``/coco/v1/info`` - :class:`.CoreInfo`

Additionally the server creates an endless loop to query collection
``sys.stat`` continuously with :class:`.QueueStatus` to support the
:class:`.QueueHandler`.

Start the server with::

    $ python core4/api/v1/server.py
"""

from core4.api.v1.application import CoreApiContainer
from core4.api.v1.request.queue.job import JobHandler
from core4.api.v1.request.queue.job import JobPost
from core4.api.v1.request.queue.job import JobStream
from core4.api.v1.request.queue.state import QueueHandler
from core4.api.v1.request.queue.state import QueueStatus
from core4.api.v1.request.role.main import RoleHandler
from core4.api.v1.request.standard.access import AccessHandler
from core4.api.v1.tool.functool import serve
from tornado.ioloop import IOLoop

# sys.stat query object
publisher = QueueStatus()
IOLoop.current().spawn_callback(publisher.update)


class CoreApiServer(CoreApiContainer):
    """
    Default :class:`.CoreApiContainer` serving the standard core4 endpoints
    at ``/coco/v1``.
    """
    root = "/coco/v1/"
    rules = [
        (r'/queue', QueueHandler, dict(source=publisher)),
        (r'/jobs/poll', JobStream),
        (r'/jobs/poll/(.*)', JobStream, None, "polling"),
        (r'/jobs', JobHandler),
        (r'/jobs/(.*)', JobHandler),
        (r'/enqueue', JobPost),
        (r'/roles', RoleHandler),
        (r'/roles/(.*)', RoleHandler),
        (r'/access', AccessHandler),
        (r'/access/(.*)', AccessHandler),
    ]


if __name__ == '__main__':
    serve(CoreApiServer)
