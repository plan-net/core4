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
from core4.api.v1.request.queue.job import JobList
from core4.api.v1.request.job import JobRequest
from core4.api.v1.request.standard.system import SystemHandler
from core4.api.v1.request.role.main import RoleHandler
from core4.api.v1.request.standard.access import AccessHandler
from core4.api.v1.request.standard.log import LogHandler
from core4.api.v1.request.standard.event import EventHandler
from core4.api.v1.request.standard.event import EventHistoryHandler
from core4.api.v1.request.standard.event import EventWatch
from core4.api.v1.request.standard.event import QueueWatch
from core4.api.v1.request.standard.login import LoginHandler
from core4.api.v1.request.standard.logout import LogoutHandler
from core4.api.v1.request.standard.profile import ProfileHandler
from core4.api.v1.request.standard.setting import SettingHandler
from core4.api.v1.request.standard.static import CoreStaticFileHandler
from core4.api.v1.request.standard.avatar import AvatarHandler
from core4.api.v1.request.store import StoreHandler
from core4.api.v1.request.standard.about import AboutHandler


class CoreAppManager(CoreApiContainer):
    root = ""
    rules = [
        (r'/comoco', CoreStaticFileHandler, {
            "path": "/webapps/comoco/dist",
            "static_path": "/webapps/comoco/dist",
            "title": "comoco",
            "subtitle": "Job Monitoring and Control",
            "tag": ["operations", "jobs"],
            "icon": "mdi-electron-framework",
            "doc": "Review and manage automation jobs"
        }),
        # the following static file handler must be the last handler
        (r'/', CoreStaticFileHandler, {
            "path": "/webapps/widgets/dist",
            "static_path": "/webapps/widgets/dist",
            "title": "App Manager",
            "subtitle": "core4os Suite",
            "tag": ["api"],
            "icon": "mdi-application",
            "doc": "Start Apps and Manage Boards",
            "target": "blank"
        })
    ]


class CoreApiServer(CoreApiContainer):
    """
    Default :class:`.CoreApiContainer` serving the standard core4 endpoints
    at ``/core4/api/v1``.
    """
    root = "/core4/api/v1"
    rules = [

        (r'/job', JobRequest),
        (r'/job/(.+)', JobRequest),

        (r'/jobs/poll', JobStream),
        (r'/jobs/poll/(.*)', JobStream, None, "JobStream"),
        (r'/jobs/list', JobList, None, "JobList"),
        (r'/jobs/history', JobHistoryHandler, None, "JobHistory"),
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

        (r'/log/?', LogHandler, None, "LogHandler"),

        (r"/login", LoginHandler),
        (r"/reset", LoginHandler),
        (r"/logout", LogoutHandler),

        (r"/profile", ProfileHandler),
        (r"/about", AboutHandler),

        (r'/setting', SettingHandler),
        (r'/setting/(.*)', SettingHandler),

        (r'/avatar', AvatarHandler),

        (r'/store', StoreHandler),
        (r'/store(\/.*)', StoreHandler),
    ]

    def on_enter(self):
        event = EventWatch()
        IOLoop.current().add_callback(event.watch)
        queue = QueueWatch()
        IOLoop.current().add_callback(queue.watch)

    def on_exit(self):
        QueueWatch.stop = True
        if EventWatch.change_stream is not None:
            IOLoop.current().run_sync(EventWatch.change_stream.close)


if __name__ == '__main__':
    from core4.api.v1.tool.functool import serve

    serve(CoreAppManager, CoreApiServer)
