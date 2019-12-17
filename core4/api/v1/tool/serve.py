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

import core4.api.v1.server
import core4.const
import core4.error
import core4.service
import core4.service.setup
import core4.util.node
from core4.api.v1.request.main import CoreBaseHandler
from core4.api.v1.server import CoreApiServer, CoreAppManager
from core4.base import CoreBase
from core4.logger import CoreLoggerMixin
from core4.service.introspect.command import SERVE
from core4.service.introspect.main import CoreIntrospector


class CoreApiServerTool(CoreBase, CoreLoggerMixin):
    """
    Helper class to :meth:`.serve` :class:`CoreApiContainer` classes.
    """

    def initialise_object(self):
        self.container = []

    def prepare(self, name=None, address=None, port=None, routing=None):
        """
        Prepare the service with

        :param name: of the service
        :param address: to listen to
        :param port: to listen to
        :param routing: masquerading domain name if behind a proxy

        :return: the configured HTTP server arguments, see core4.config.api
        """
        self.startup = core4.util.node.mongo_now()

        self.setup_logging()
        core4.service.setup.CoreSetup().make_all()

        # http server settings
        http_args = {}
        cert_file = self.config.api.crt_file
        key_file = self.config.api.key_file
        # global settings
        name = name or "app"
        self.identifier = "@".join([name, core4.util.node.get_hostname()])
        self.port = int(port or self.config.api.port)
        self.address = address or "0.0.0.0"
        self.hostname = core4.util.node.get_hostname()
        if cert_file and key_file:
            self.logger.info("securing server with [%s]", cert_file)
            http_args["ssl_options"] = {
                "certfile": cert_file,
                "keyfile": key_file,
            }
            protocol = "https"
        else:
            protocol = "http"
        if routing is None:
            routing = "%s://%s:%d" % (protocol, self.address, self.port)
        if routing.endswith("/"):
            self.routing = routing[:-1]
        else:
            self.routing = routing
        return http_args

    def start_http(self, http_args, router, reuse_port=True):
        """
        Starts the HTTP server with the passed arguments

        :return: HTTP server instance
        """
        server = tornado.httpserver.HTTPServer(router, **http_args)
        server.bind(self.port, address=self.address, reuse_port=reuse_port)
        server.start()
        self.logger.info("open %ssecure socket on port [%s:%d] routed at [%s]",
                         "" if http_args.get("ssl_options") else "NOT ",
                         self.address, self.port, self.routing)
        return server

    def serve(self, *args, port=None, address=None, name=None, reuse_port=True,
              routing=None, core4api=True, **kwargs):
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
        :param kwargs: to be passed to all :class:`CoreApiApplication`
        """
        self.create_routes(*args, port=port, address=address, name=name,
                           reuse_port=reuse_port, routing=routing,
                           core4api=core4api, **kwargs)
        self.init_callback()
        self.start_loop()

    def init_callback(self):
        """
        Adds :meth:`.heartbeat` to the ioloop.
        """
        tornado.ioloop.IOLoop.current().spawn_callback(self.heartbeat)

    def start_loop(self):
        """
        Starts the ioloop
        """
        try:
            tornado.ioloop.IOLoop().current().start()
        except KeyboardInterrupt:
            raise SystemExit()
        except:
            raise
        finally:
            self.unregister()
            tornado.ioloop.IOLoop().current().stop()

    def create_routes(self, *args, name=None, address=None, port=None,
                      routing=None, core4api=False, reuse_port=True, **kwargs):
        """
        Instantiates the passed :class:`.CoreApiContainer`, adds the default
        containers :class:`.CoreApiServer` and :class:`.CoreAppManager`
        (if ``core4api is True``, defaults to ``False``), registers all
        handlers and starts the HTTP server.

        :param args: :class:`.CoreApiContainer`
        :param name: of the tornado service, defaults to ``app``
        :param address: to listen to, defaults to ``0.0.0.0``
        :param port: to listen to, see core4.config.api.port
        :param routing: masquerading domain name if serving behind a load
                        balancer
        :param core4api: ``True`` to append default containers, defaults to
                         ``False``
        :param reuse_port: tells the kernel to reuse a local socket in
                           ``TIME_WAIT`` state, defaults to ``True``
        :param kwargs: keyword arguments to be passed with instantiation of
                       each :class:`.CoreApplication`
        :return: HTTP server instance
        """
        http_args = self.prepare(name, address, port, routing)
        routes = []
        container_list = []
        for container_cls in args:
            if isinstance(container_cls, str):
                modname = ".".join(container_cls.split(".")[:-1])
                clsname = container_cls.split(".")[-1]
                module = importlib.import_module(modname)
                container_cls = getattr(module, clsname)
            container_list.append(container_cls)
        if core4api:
            qual_names = [a.qual_name() for a in container_list]
            for addon in (CoreApiServer, CoreAppManager):
                if addon.qual_name() not in qual_names:
                    container_list.append(addon)
        # fix routing order
        container_list.sort(key=lambda r: r.get_root(), reverse=True)
        for container_cls in container_list:
            if not container_cls.enabled:
                self.logger.warning("skipping NOT enabled container [%s]",
                                    container_cls.qual_name())
                continue
            if isinstance(container_cls, str):
                modname = ".".join(container_cls.split(".")[:-1])
                clsname = container_cls.split(".")[-1]
                module = importlib.import_module(modname)
                container_cls = getattr(module, clsname)
            container_obj = container_cls(routing=self.routing, **kwargs)
            root = container_obj.get_root()
            application = container_obj.make_application()
            if root in [c.get_root() for c in self.container]:
                raise core4.error.Core4SetupError(
                    "routing root [{}] already exists [{}]".format(
                        root, container_cls.qual_name())
                )
            self.container.append(container_obj)
            self.logger.info("successfully registered container [%s] at [%s]",
                             container_cls.qual_name(), root + ".*")
            routes.append(
                tornado.routing.Rule(tornado.routing.PathMatches(
                    root + ".*"), application)
            )
        router = tornado.routing.RuleRouter(routes)
        self.register(router)
        for obj in self.container:
            obj.on_enter()
        return self.start_http(http_args, router, reuse_port)

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
            cnt = await sys_worker.count_documents(
                {"_id": "__halt__", "timestamp": {"$gte": self.startup}})
            if cnt > 0:
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
                        hostname=self.hostname,
                        port=self.port,
                        routing=self.routing,

                        started_at=self.startup,
                        container=[],
                        rsc_id=rule.rsc_id,

                        author=handler.author,
                        version=handler.version(),
                        project=handler.get_project(),
                        protected=handler.protected,
                        qual_name=handler.qual_name(),
                        tag=handler.tag,
                        title=handler.title,
                        subtitle=handler.subtitle,
                        enter_url=handler.enter_url,
                        target=handler.target,
                        spa=handler.spa
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
        Spawns :meth:`.CoreApiContainer.exit` for each registered api container
        and Unregisters all endpoints of the tornado server in ``sys.handler``.
        """
        total, reset = self.reset_handler()
        for obj in self.container:
            obj.on_exit()
        self.logger.info("unregistering server [%s] with [%d] handlers, "
                         "[%d] reset", self.identifier, total, reset)

    def serve_all(self, project=None, filter=None, port=None, address=None,
                  name=None, reuse_port=True, routing=None, **kwargs):
        """
        Starts the tornado HTTP server listening on the specified port and
        enters tornado's IOLoop.

        :param project: containing the :class:`.CoreApiContainer` to serve,
                        defaults to ``core4``
        :param filter: list of str matching the :class:`.CoreApiContainer`
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
        """
        if not filter:
            filter = [None]
        scope = []
        intro = CoreIntrospector()
        for f in filter:
            for pro in intro.introspect(project):
                for container in pro["api_containers"]:
                    if f is None or container["name"].startswith(f):
                        if container["name"] not in scope:
                            scope.append(container["name"])
        if scope:
            args = dict(
                port=port,
                address=address,
                name=name,
                reuse_port=reuse_port,
                routing=routing,
            )
            args.update(kwargs)
            if project:
                core4.service.introspect.main.exec_project(
                    project, SERVE, a=scope, kw=args, replace=True)
            else:
                self.serve(*scope, core4api=False, **args, replace=False)
