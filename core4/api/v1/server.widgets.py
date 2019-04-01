#
# Copyright 2019 Plan.Net Business Intelligence GmbH & Co. KG
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
    $ python core4/api/v1/server.widget.py
"""

from tornado.ioloop import IOLoop

from core4.api.v1.application import CoreApiContainer
from core4.api.v1.request.standard.event import EventWatch
from core4.api.v1.request.standard.event import QueueWatch
from core4.api.v1.tool.functool import serve
from core4.api.v1.request.static import CoreStaticFileHandler


event = EventWatch()
IOLoop.current().add_callback(event.watch)
queue = QueueWatch()
IOLoop.current().add_callback(queue.watch)


def close_watchers():
    event.change_stream.close()


class CoreApiServer(CoreApiContainer):
    """
    Default :class:`.CoreApiContainer` serving the standard core4 endpoints
    at ``/core4/api/v1``.
    """
    root = "/core4/api/v1"
    rules = [
        ("/widgets", CoreStaticFileHandler, {"path": "./request/_static/widgets/dist", "protected": True, "title": "core widgets"})
    ]

    def on_exit(self):
        event.change_stream.close()


if __name__ == '__main__':
    serve(CoreApiServer, routing="localhost:5001", address="0.0.0.0")

