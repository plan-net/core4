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
from core4.api.v1.request.queue.history import JobHistoryHandler
from core4.api.v1.request.queue.history import QueueHistoryHandler
from core4.api.v1.request.queue.job import JobHandler
from core4.api.v1.request.queue.job import JobPost
from core4.api.v1.request.queue.job import JobStream
from core4.api.v1.request.standard.system import SystemHandler
from core4.api.v1.request.role.main import RoleHandler
from core4.api.v1.request.standard.access import AccessHandler
from core4.api.v1.request.standard.event import EventHandler
from core4.api.v1.request.standard.event import EventHistoryHandler
from core4.api.v1.request.standard.event import EventWatch
from core4.api.v1.request.standard.event import QueueWatch
from core4.api.v1.request.standard.login import LoginHandler
from core4.api.v1.request.standard.logout import LogoutHandler
from core4.api.v1.request.standard.profile import ProfileHandler
from core4.api.v1.request.standard.setting import SettingHandler
from core4.api.v1.request.static import CoreStaticFileHandler

from core4.api.v1.request.link import CoreLinkHandler


class CoreAppManager(CoreApiContainer):
    root = ""
    rules = [
        (r'/comoco', CoreStaticFileHandler, {
            "path": "/webapps/comoco/dist",
            "static_path": "/webapps/comoco/dist",
            "title": "monitoring and control (comoco)",
            "tag": "jobs app",
            "protected": False
        }),
        (r'/about', CoreLinkHandler, {
            "enter_url": "https://core4os.readthedocs.io/en/latest/about.html",
            "doc":  "About core4os at readthedocs",
            "author": "mra",
            "tag": ["info"],
            "title": "about core4os"
        }),
        # the following static file handler must be the last handler
        (r'/', CoreStaticFileHandler, {
            "path": "/webapps/widgets/dist",
            "static_path": "/webapps/widgets/dist",
            "title": "root",
            "protected": False
        })
    ]


class CoreApiServer(CoreApiContainer):
    """
    Default :class:`.CoreApiContainer` serving the standard core4 endpoints
    at ``/core4/api/v1``.
    """
    root = "/core4/api/v1"
    rules = [
        (r'/jobs/poll', JobStream),
        (r'/jobs/poll/(.*)', JobStream, None, "JobStream"),
        (r'/jobs/history', JobHistoryHandler),
        (r'/jobs/history/(.*)', JobHistoryHandler, None, "JobHistory"),
        (r'/jobs/enqueue/?', JobPost),
        (r'/jobs', JobHandler),
        (r'/jobs/(.*)', JobHandler, None, "JobHandler"),

        (r'/queue/history', QueueHistoryHandler),
        (r'/queue/history(.*)', QueueHistoryHandler, None, "QueueHistory"),

        (r'/system/?', SystemHandler),

        (r'/roles', RoleHandler),
        (r'/roles/(.*)', RoleHandler, None, "RoleHandler"),

        (r'/access', AccessHandler),
        (r'/access/(.*)', AccessHandler, None, "AccessHandler"),

        (r'/event/history/?', EventHistoryHandler, None),
        (r'/event/?', EventHandler, None),

        (r"/login", LoginHandler),
        (r"/logout", LogoutHandler),

        (r"/profile", ProfileHandler),

        (r'/setting', SettingHandler),
        (r'/setting/(.*)', SettingHandler),

    ]

    def on_enter(self):
        event = EventWatch()
        IOLoop.current().add_callback(event.watch)
        queue = QueueWatch()
        IOLoop.current().add_callback(queue.watch)

    def on_exit(self):
        QueueWatch.stop = True
        if EventWatch.change_stream is not None:
            EventWatch.change_stream.close()


if __name__ == '__main__':
    from core4.api.v1.tool.functool import serve

    serve(CoreAppManager, CoreApiServer)
