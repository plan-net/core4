#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Implements :class:`.CoreApiServerTool to serve one or multiple
:class:`.CoreApiContainer` with their :class:`.CoreApplication`.
"""

import importlib

import tornado.httpserver
import tornado.ioloop
import tornado.routing
from tornado import gen

import core4.const
import core4.error
import core4.service
import core4.util.node
from core4.api.v1.application import RootContainer
from core4.base import CoreBase
from core4.api.v1.request.main import CoreBaseHandler
from core4.logger import CoreLoggerMixin
from core4.util.data import rst2html


class CoreApiServerTool(CoreBase, CoreLoggerMixin):
    """
    Helper class to :meth:`.serve` :class:`CoreApiContainer` classes.
    """

    def make_routes(self, *args, **kwargs):
        """
        Based on the list of :class:`.CoreApiContainer` classes this method
        creates the required routing :class:`tornado.routing.RuleRouter`
        objects prefixed with the containers` prefix :attr:`.root` property.

        :param args: list of :class:`.CoreApiContainer` classes
        :param kwargs: keyword arguments to be passed to the
                       :class:`CoreApplication` instances derived from
                       :class:`tornado.web.Application`
        :return: :class:`tornado.routing.RuleRouter` object
        """
        routes = []
        roots = set()
        RootContainer.routes = {}
        RootContainer.application = {}
        for container_cls in list(args) + [RootContainer]:
            container_obj = container_cls(**kwargs)
            root = container_obj.get_root()
            if not container_obj.enabled:
                self.logger.warning("starting NOT enabled container [%s]",
                                    container_obj.qual_name())
            if root in roots:
                raise core4.error.Core4SetupError(
                    "routing root [{}] already exists [{}]".format(
                        root, container_cls.qual_name())
                )
            self.logger.info("successfully registered container [%s]",
                             container_cls.qual_name())
            application = container_obj.make_application()
            routes.append(
                tornado.routing.Rule(tornado.routing.PathMatches(
                    root + ".*"), application)
            )
            roots.add(root)
        return tornado.routing.RuleRouter(routes)

    def serve(self, *args, port=None, address=None, name=None, reuse_port=True,
              routing=None, on_exit=None, **kwargs):
        """
        Starts the tornado HTTP server listening on the specified port and
        enters tornado's IOLoop.

        :param args: one or more :class:`CoreApiContainer` classes
        :param port: to listen, defaults to ``5001``, see core4 configuration
                     setting ``api.port``
        :param address: IP address or hostname.  If it's a hostname, the server
                        will listen on all IP addresses associated with the
                        name.  Address may be an empty string or None to listen
                        on all  available interfaces.
        :param name: to identify the server
        :param reuse_port: tells the kernel to reuse a local socket in
                           ``TIME_WAIT`` state, defaults to ``True``
        :param routing: URL including the protocol and hostname of the server,
                        defaults to the protocol depending on SSL settings, the
                        node hostname or address and port
        :param on_exit: callback function which will be called at server exit
        :param kwargs: to be passed to all :class:`CoreApiApplication`
        """
        self.startup = core4.util.node.mongo_now()
        self.setup_logging()
        setup = core4.service.setup.CoreSetup()
        setup.make_all()

        name = name or "app"
        self.identifier = "@".join([name, core4.util.node.get_hostname()])
        self.hostname = core4.util.node.get_hostname()
        self.port = port or self.config.api.port
        self.address = address or self.hostname

        http_args = {}
        cert_file = self.config.api.crt_file
        key_file = self.config.api.key_file
        if cert_file and key_file:
            self.logger.info("securing server with [%s]", cert_file)
            http_args["ssl_options"] = {
                "certfile": cert_file,
                "keyfile": key_file,
            }
            self.protocol = "https"
        else:
            self.protocol = "http"

        self.routing = routing or "%s:%d" % (self.address, self.port)
        self.routing = self.protocol + "://" + self.routing
        if self.routing.endswith("/"):
            self.routing = self.routing[:-1]

        self.router = self.make_routes(*args, **kwargs)

        server = tornado.httpserver.HTTPServer(self.router, **http_args)
        server.bind(self.port, address=self.address, reuse_port=reuse_port)
        server.start()
        self.logger.info("open %ssecure socket on port [%d]",
                         "" if http_args.get("ssl_options") else "NOT ",
                         self.port)
        self.register()
        tornado.ioloop.IOLoop.current().spawn_callback(self.heartbeat)
        try:
            tornado.ioloop.IOLoop().current().start()
        except KeyboardInterrupt:
            tornado.ioloop.IOLoop().current().stop()
            raise SystemExit()
        except:
            raise
        finally:
            self.unregister()
            if on_exit is not None:
                on_exit()

    async def heartbeat(self):
        """
        Sets the heartbeat of the tornado server/container in ``sys.worker`` as
        defined by core4 configuration key ``daemon.heartbeat``.
        """
        sys_worker = self.config.sys.worker.connect_async()
        sleep = self.config.daemon.heartbeat
        await sys_worker.update_one(
            {"_id": self.identifier},
            update={"$set": {
                "heartbeat": None,
                "hostname": self.hostname,
                "protocol": self.protocol,
                "address": self.address,
                "port": self.port,
                "kind": "app",
                "pid": core4.util.node.get_pid(),
                "phase": {
                    "startup": self.startup,
                    "loop": core4.util.node.mongo_now(),
                    "shutdown": None,
                    "exit": None
                }
            }},
            upsert=True
        )
        while True:
            nxt = gen.sleep(sleep)
            doc = await sys_worker.find_one(
                {"_id": "__halt__", "timestamp": {"$gte": self.startup}})
            if doc is not None:
                self.logger.debug("stop IOLoop now")
                break
            await sys_worker.update_one(
                {"_id": self.identifier},
                {"$set": {"heartbeat": core4.util.node.mongo_now()}})
            await nxt
        await sys_worker.update_one(
            {"_id": self.identifier},
            update={"$set": {
                "phase.shutdown": core4.util.node.mongo_now(),
                "phase.exit": core4.util.node.mongo_now()
            }}
        )
        # await sys_worker.delete_one({"_id": self.routing})
        tornado.ioloop.IOLoop.current().stop()

    def register(self):
        """
        Registers all endpoints of the tornado server in ``sys.handler``.
        """
        self.logger.info("registering server [%s] at [%s]", self.identifier,
                         self.routing)
        update = {}
        for md5_route, routes in RootContainer.routes.items():
            for (app, container, specs) in routes:
                pattern = specs.matcher.regex.pattern
                cls = specs.target
                if issubclass(cls, CoreBaseHandler):
                    args = specs.target_kwargs
                    html = rst2html(str(cls.__doc__))
                    doc = dict(
                        routing=self.routing,
                        args=str(args),
                        author=cls.author,
                        container=container.qual_name(),
                        description=html["body"],
                        error=html["error"],
                        icon=cls.icon,
                        project=cls.get_project(),
                        protected=cls.protected,
                        protocol=self.protocol,
                        qual_name=cls.qual_name(),
                        tag=cls.tag,
                        title=cls.title,
                        version=cls.version(),
                        started_at=self.startup
                    )
                    if args:
                        for attr in cls.propagate:
                            if attr in doc:
                                doc[attr] = args.get(attr, doc[attr])
                    lookup = (self.hostname, self.port, md5_route)
                    if lookup not in update:
                        doc["pattern"] = []
                        update[lookup] = doc
                    update[lookup]["pattern"].append((specs.name, pattern))
            self.reset_handler()
            coll = self.config.sys.handler
            for lookup, doc in update.items():
                coll.update_one(
                    {
                        "hostname": lookup[0],
                        "port": lookup[1],
                        "route_id": lookup[2]
                    },
                    {
                        "$set": doc,
                        "$setOnInsert": {
                            "created_at": self.startup
                        }
                    },
                    upsert=True
                )

    def reset_handler(self):
        """
        Removes all registered handlers
        :return:
        """
        self.config.sys.handler.update_many(
            {"hostname": self.hostname, "port": self.port},
            {"$set": {"started_at": None}}
        )

    def unregister(self):
        """
        Unregisters all endpoints of the tornado server in ``sys.handler``.
        """
        self.logger.info("unregistering server [%s]", self.identifier)
        self.reset_handler()

    def serve_all(self, filter=None, port=None, address=None, name=None,
                  reuse_port=True, routing=None, on_exit=None, **kwargs):
        """
        Starts the tornado HTTP server listening on the specified port and
        enters tornado's IOLoop.

        :param filter: one or more str matching the :class:`.CoreApiContainer`
                       :meth:`.qual_name <core4.base.main.CoreBase.qual_name>`
        :param port: to listen, defaults to ``5001``, see core4 configuration
                     setting ``api.port``
        :param address: IP address or hostname.  If it's a hostname, the server
                        will listen on all IP addresses associated with the
                        name.  Address may be an empty string or None to listen
                        on all  available interfaces.
        :param name: to identify the server
        :param reuse_port: tells the kernel to reuse a local socket in
                           ``TIME_WAIT`` state, defaults to ``True``
        :param routing: URL including the protocol and hostname of the server,
                        defaults to the protocol depending on SSL settings, the
                        node hostname or address and port
        :param on_exit: callback function which will be called at server exit
        :param kwargs: to be passed to all :class:`CoreApiApplication`
        """
        self.setup_logging()
        intro = core4.service.introspect.CoreIntrospector()
        if filter is not None:
            if not isinstance(filter, list):
                filter = [filter]
            for i in range(len(filter)):
                if not filter[i].endswith("."):
                    filter[i] += "."
        scope = []
        for api in intro.iter_api_container():
            if filter is None:
                scope.append(api)
            else:
                if not isinstance(filter, list):
                    filter = [filter]
                for f in filter:
                    if api["name"].startswith(f):
                        scope.append(api)
                        break
        clist = []
        for api in scope:
            modname = ".".join(api["name"].split(".")[:-1])
            clsname = api["name"].split(".")[-1]
            module = importlib.import_module(modname)
            cls = getattr(module, clsname)
            self.logger.debug("added [%s]", api["name"])
            clist.append(cls)
        if scope:
            self.serve(*clist, port=port, name=name, address=address,
                       reuse_port=reuse_port, routing=routing, on_exit=on_exit,
                       **kwargs)
