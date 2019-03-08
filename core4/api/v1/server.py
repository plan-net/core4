#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Delivers the default core4 API server. This server roots to ``/core4/api``
and provides the following endpoints:

* ``/core4/api/v1/queue`` - :class:`.QueueHandler`
* ``/core4/api/v1/jobs`` - :class:`.JobHandler`
* ``/core4/api/v1/jobs/poll`` - :class:`.JobStream`
* ``/core4/api/v1/enqueue`` - :class:`.JobPost`
* ``/core4/api/v1/roles`` - :class:`.RoleHandler`
* ``/core4/api/v1/access`` - :class:`.AcceHandlerr`

Additionally the server creates an endless loop to query collection
``sys.event`` continuously with :class:`.EventWatch` to support the
:class:`.EventHandler`.

Start the server with::

    $ python core4/api/v1/server.py
"""

from tornado.ioloop import IOLoop

from core4.api.v1.application import CoreApiContainer
from core4.api.v1.request.queue.job import JobHandler
from core4.api.v1.request.queue.job import JobPost
from core4.api.v1.request.queue.job import JobStream
from core4.api.v1.request.role.main import RoleHandler
from core4.api.v1.request.standard.access import AccessHandler
from core4.api.v1.request.standard.event import EventHandler
from core4.api.v1.request.standard.event import EventWatch
from core4.api.v1.request.standard.event import QueueWatch
from core4.api.v1.tool.functool import serve

event = EventWatch()
IOLoop.current().add_callback(event.watch)
queue = QueueWatch()
IOLoop.current().add_callback(queue.watch)


class CoreApiServer(CoreApiContainer):
    """
    Default :class:`.CoreApiContainer` serving the standard core4 endpoints
    at ``/core4/api/v1``.
    """
    root = "/core4/api/v1"
    rules = [
        (r'/jobs/poll', JobStream),
        (r'/jobs/poll/(.*)', JobStream, None, "JobStream"),
        (r'/jobs', JobHandler),
        (r'/jobs/(.*)', JobHandler, None, "JobHandler"),
        (r'/enqueue', JobPost),
        (r'/roles', RoleHandler),
        (r'/roles/(.*)', RoleHandler, None, "RoleHandler"),
        (r'/access', AccessHandler),
        (r'/access/(.*)', AccessHandler, None, "AccessHandler"),
        (r'/event', EventHandler, None, "EventHandler"),
    ]


if __name__ == '__main__':
    serve(CoreApiServer)
