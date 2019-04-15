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

import core4.api.v1.server
import core4.const
import core4.error
import core4.service
import core4.service.introspect
import core4.service.setup
import core4.util.node
import tornado.httpserver
import tornado.ioloop
import tornado.routing
from core4.api.v1.request.main import CoreBaseHandler
from core4.api.v1.server import CoreApiServer
from core4.base import CoreBase
from core4.logger import CoreLoggerMixin
from core4.service.introspect.command import SERVE
from tornado import gen


class CoreApiServerTool(CoreBase, CoreLoggerMixin):
    """
    Helper class to :meth:`.serve` :class:`CoreApiContainer` classes.
    """

    def prepare(self, name, address, port, routing):
        self.startup = core4.util.node.mongo_now()

        self.setup_logging()
        core4.service.setup.CoreSetup().make_all()

        # http server settings
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

        # global settings
        name = name or "app"
        self.identifier = "@".join([name, core4.util.node.get_hostname()])
        self.port = int(port or self.config.api.port)
        self.address = address or "0.0.0.0"
        self.hostname = core4.util.node.get_hostname()
        self.routing = "{}://{}".format(
            self.protocol, routing or "%s:%d" % (self.address, self.port))
        if self.routing.endswith("/"):
            self.routing = self.routing[:-1]
        return http_args

    def start_http(self, http_args, router, reuse_port):
        server = tornado.httpserver.HTTPServer(router, **http_args)
        server.bind(self.port, address=self.address, reuse_port=reuse_port)
        server.start()
        self.logger.info("open %ssecure socket on port [%s:%d] routed at [%s]",
                         "" if http_args.get("ssl_options") else "NOT ",
                         self.address, self.port, self.routing)

    def serve(self, *args, port=None, address=None, name=None, reuse_port=True,
              routing=None, core4api=False, **kwargs):
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
        http_args = self.prepare(name, address, port, routing)
        routes = []
        container = []
        if core4api:
            qual_names = [a.qual_name() for a in args]
            if CoreApiServer.qual_name() not in qual_names:
                args = list(args)
                args.append(core4.api.v1.server.CoreApiServer)
        for container_cls in args:
            if not container_cls.enabled:
                self.logger.warning("starting NOT enabled container [%s]",
                                    container_cls.qual_name())
                continue
            if isinstance(container_cls, str):
                modname = ".".join(container_cls.split(".")[:-1])
                clsname = container_cls.split(".")[-1]
                module = importlib.import_module(modname)
                container_cls = getattr(module, clsname)
            container_obj = container_cls(**kwargs)
            root = container_obj.get_root()
            application = container_obj.make_application()
            if root in [c.get_root() for c in container]:
                raise core4.error.Core4SetupError(
                    "routing root [{}] already exists [{}]".format(
                        root, container_cls.qual_name())
                )
            container.append(container_obj)
            self.logger.info("successfully registered container [%s]",
                             container_cls.qual_name())
            routes.append(
                tornado.routing.Rule(tornado.routing.PathMatches(
                    root + ".*"), application)
            )
        router = tornado.routing.RuleRouter(routes)
        self.register(router)
        self.start_http(http_args, router, reuse_port)
        tornado.ioloop.IOLoop.current().spawn_callback(self.heartbeat)
        try:
            tornado.ioloop.IOLoop().current().start()
        except KeyboardInterrupt:
            tornado.ioloop.IOLoop().current().stop()
            raise SystemExit()
        except:
            tornado.ioloop.IOLoop().current().stop()
            raise
        finally:
            self.unregister()
            for obj in container:
                obj.on_exit()

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
                "routing": self.routing,
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

    def register(self, router):
        """
        Registers all endpoints of the tornado server in ``sys.handler``.
        """
        self.logger.info("registering server [%s] at [%s]", self.identifier,
                         self.routing)
        coll = self.config.sys.handler
        total, reset = self.reset_handler()
        created = 0
        updated = 0
        data = {}
        for app in router.rules:
            for rule in app.target.wildcard_router.rules:
                handler = rule.target
                if issubclass(handler, CoreBaseHandler):
                    doc = dict(
                        protocol=self.protocol,
                        hostname=self.hostname,
                        port=self.port,
                        routing=self.routing,

                        started_at=self.startup,
                        container=[],
                        rsc_id=rule.rsc_id,

                        author=handler.author,
                        icon=handler.icon,
                        project=handler.get_project(),
                        protected=handler.protected,
                        qual_name=handler.qual_name(),
                        tag=handler.tag,
                        title=handler.title,
                        version=handler.version()
                    )
                    # respect and populate handler arguments to overwrite
                    for attr, value in rule.target_kwargs.items():
                        if attr in handler.propagate and attr in doc:
                            doc[attr] = value
                    data.setdefault(rule.rsc_id, doc)
                    data[rule.rsc_id]["container"].append(
                        (app.target.container.qual_name(),
                         rule.matcher.regex.pattern,
                         app.target.container.get_root(),
                         rule.name))
        for rsc_id, doc in data.items():
            ret = coll.update_one(
                filter={
                    "hostname": self.hostname,
                    "port": self.port,
                    "rsc_id": rsc_id
                },
                update={
                    "$set": doc,
                    "$setOnInsert": {
                        "created_at": self.startup
                    }
                },
                upsert=True
            )
            if ret.upserted_id:
                created += 1
            else:
                updated += 1

        self.logger.info("found [%s] application, handlers registered [%d], "
                         "reset [%d], updated [%d], created [%d]",
                         len(router.rules), total, reset, updated, created)

    def reset_handler(self):
        """
        Removes all registered handlers
        :return:
        """
        ret = self.config.sys.handler.update_many(
            {"hostname": self.hostname, "port": self.port},
            {"$set": {"started_at": None}}
        )
        return ret.matched_count, ret.modified_count

    def unregister(self):
        """
        Unregisters all endpoints of the tornado server in ``sys.handler``.
        """
        total, reset = self.reset_handler()
        self.logger.info("unregistering server [%s] with [%d] handlers, "
                         "[%d] reset", self.identifier, total, reset)

    def serve_all(self, project=None, filter=None, port=None, address=None,
                  name=None, reuse_port=True, routing=None):
        """
        todo: docs require update
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
        if not project:
            project = self.project
        if filter is None:
            filter = [project]
        for i in range(len(filter)):
            if not filter[i].endswith("."):
                filter[i] += "."
        scope = []
        intro = core4.service.introspect.CoreIntrospector()
        for project, data in intro.list_project(project):
            for container in data["container"]:
                if not filter:
                    scope.append(container["name"])
                else:
                    for f in filter:
                        if container["name"].startswith(f):
                            scope.append(container["name"])
                            break
        if scope:
            args = dict(
                port=port,
                address=address,
                name=name,
                reuse_port=reuse_port,
                routing=routing,
            )
            core4.service.introspect.exec_project(project, SERVE, a=scope,
                                                  kw=args)
