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
from core4.api.v1.request.link import CoreLinkHandler


class CoreAppManager(CoreApiContainer):
    root = ""
    rules = [
        (r'/comoco', CoreStaticFileHandler, {
            "path": "/webapps/comoco/dist",
            "static_path": "/webapps/comoco/dist",
            "title": "monitoring and control (comoco)",
            "tag": "jobs app",
            "protected": True
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
            "protected": True
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

        (r'/log/?', LogHandler, None, "LogHandler"),

        (r"/login", LoginHandler),
        (r"/reset", LoginHandler),
        (r"/logout", LogoutHandler),

        (r"/profile", ProfileHandler),

        (r'/setting', SettingHandler),
        (r'/setting/(.*)', SettingHandler),

        (r'/avatar', AvatarHandler),
        (r'/avatar/(.*)', AvatarHandler),

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
"""
    import core4.queue.main
    import datetime
    import pandas as pd

    def load_data():
        from collections import OrderedDict
        q = core4.queue.main.CoreQueue()
        coll = q.config.sys.event
        cur = coll.aggregate([
            {
                "$match": {
                    "created": {
                        "$gte": datetime.datetime.utcnow() - datetime.timedelta(days=30)
                    },
                    "data.queue": {
                        "$exists": True
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "created": "$created",
                    "pending": {"$exists": ["$data.queue.pending", 0]},
                    "running": {"$exists": ["$data.queue.running",
                    "deferred": "{"$exists": [$data.queue.deferred",
                    "failed": "$data.queue.failed",
                    "inactive": "$data.queue.inactive",
                    "error": "$data.queue.error",
                    "killed": "$data.queue.killed",
                }
            }
            {
                "$addFields": {
                    "total": {
                        "$add": []
                    }
                }
            }
            {
                "$sort": OrderedDict([("_id", -1), ("total", -1), ("running", -1)])
            },
            {
                "$project": {
                    "_id": 0,
                    "created": "$created",
                    "pending": "$data.queue.pending",
                    "running": "$data.queue.running",
                    "deferred": "$data.queue.deferred",
                    "failed": "$data.queue.failed",
                    "inactive": "$data.queue.inactive",
                    "error": "$data.queue.error",
                    "killed": "$data.queue.killed",
                }
            }
            {
                "$group": {
                    "_id": "$timestamp",

                    "pending": {"$sum": "$queue.pending"},
                    "running": {"$sum": "$queue.running"},
                    "deferred": {"$sum": "$queue.deferred"},
                    "failed": {"$sum": "$queue.failed"},
                    "inactive": {"$sum": "$queue.inactive"},
                    "error": {"$sum": "$queue.error"},
                    "killed": {"$sum": "$queue.killed"},

                    "start": {"$first": "$created"},
                    "end": {"$last": "$created"},
                }
            }
        ])
        #print(coll.count_documents({}))
        data = list(cur)
        from pprint import pprint
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df._id)
        # df.set_index("timestamp", inplace=True)
        # df.sort_index(inplace=True)
        #df.ffill(inplace=True)
        df.fillna(0., inplace=True)
        df.sort_values(["timestamp"], inplace=True)
        df.to_pickle("/tmp/df.pickle")
        return df


    df = load_data()
    df = pd.read_pickle("/tmp/df.pickle")
    COLS = ['pending', 'running', 'deferred', 'failed', 'inactive', 'killed',
            'error']
    df["total"] = df[COLS].sum(axis=1)
    from bokeh.io import show
    from bokeh.layouts import column
    from bokeh.models import ColumnDataSource, RangeTool
    from bokeh.palettes import brewer
    from bokeh.plotting import figure
    p = figure(plot_height=300, plot_width=1400,
               tools="xpan,box_zoom,reset", toolbar_location="right",
               x_axis_type="datetime", x_axis_location="below",
               background_fill_color="#efefef",
               y_range=(df.total.min(), df.total.max()),
               x_range=(df.timestamp.iloc[-1*int(df.shape[0] * 0.25)],
                        df.timestamp.iloc[-1]))
    print(df.tail(20).to_string())
    p.varea_stack(COLS, x='timestamp', color=brewer["Spectral"][7], source=df)

    from bokeh.io import show
    from bokeh.layouts import column
    from bokeh.models import RangeTool
    from bokeh.plotting import figure

    select = figure(plot_height=130, plot_width=1400, y_range=(df.total.min(), df.total.max()),
                    x_axis_type="datetime", y_axis_type=None,
                    tools="", toolbar_location=None, background_fill_color="#efefef")

    range_tool = RangeTool(x_range=p.x_range)
    range_tool.overlay.fill_color = "navy"
    range_tool.overlay.fill_alpha = 0.2
    select.varea_stack(["total"], x='timestamp', color="navy", source=df)
    #select.line("timestamp", "total", source=df, line_width=1)

    select.ygrid.grid_line_color = None
    select.add_tools(range_tool)
    select.toolbar.active_multi = range_tool

    show(column(p, select))
    print(df.shape)

    cur = coll.aggregate([
        {
            "$match": {
                "created": {
                    "$gte": datetime.datetime.utcnow() - datetime.timedelta(
                        days=30)
                },
                "data.queue": {
                    "$exists": True
                }
            }
        },
        {
            "$sort": {"_id": -1}
        },
        {
            "$project": {
                "_id": 0,
                "created": "$created",
                "pending": "$data.queue.pending",
                "running": "$data.queue.running",
                "deferred": "$data.queue.deferred",
                "failed": "$data.queue.failed",
                "inactive": "$data.queue.inactive",
                "error": "$data.queue.error",
                "killed": "$data.queue.killed",
                #"name": 1
       }
    }])
    data = list(cur)

    df = pd.DataFrame(data)
    df.fillna(0., inplace=True)
    df["total"] = df.sum(axis=1)
    df["ts"] = df.created.dt.strftime("%Y-%m-%dT%H:%M")
    df.drop(["created"], axis=1, inplace=True)
    df.sort_values(
        ["ts", "total", "running", "pending"],
        ascending=[True, False, False, True],
        inplace=True)
    g = df.groupby(["ts"]).first()
    g.reset_index(inplace=True)
    g["ts"] = pd.to_datetime(g.ts)

    from bokeh.io import show
    from bokeh.layouts import column
    from bokeh.palettes import brewer
    from bokeh.plotting import figure
    from bokeh.io import show
    from bokeh.layouts import column
    from bokeh.models import RangeTool
    from bokeh.plotting import figure

    p = figure(plot_height=300, plot_width=1400,
               tools="xpan,box_zoom,reset", toolbar_location="right",
               x_axis_type="datetime", x_axis_location="below",
               background_fill_color="#efefef",
               y_range=(g.total.min(), g.total.max()),
               x_range=(g.ts.iloc[-1*int(g.shape[0] * 0.25)],
                        g.ts.iloc[-1]))

    COLS = ['pending', 'running', 'deferred', 'failed', 'inactive', 'killed',
            'error']
    p.varea_stack(COLS, x='ts', color=brewer["Spectral"][7], source=g)
    select = figure(plot_height=130, plot_width=1400,
                    y_range=(g.total.min(), g.total.max()),
                    x_axis_type="datetime", y_axis_type=None,
                    tools="", toolbar_location=None, background_fill_color="#efefef")
    range_tool = RangeTool(x_range=p.x_range)
    range_tool.overlay.fill_color = "navy"
    range_tool.overlay.fill_alpha = 0.2
    select.varea_stack(["total"], x='ts', color="navy", source=g)

    select.ygrid.grid_line_color = None
    select.add_tools(range_tool)
    select.toolbar.active_multi = range_tool

    show(column(p, select))
"""

