from concurrent.futures import ThreadPoolExecutor

import tornado.routing
import tornado.web

import core4.error
import core4.logger.mixin
import core4.service.setup
from core4.api.v1.request.default import DefaultHandler
from core4.base.main import CoreBase

LOGIN_URL = "/core4/login"


class CoreApplication(tornado.web.Application):

    def __init__(self, handlers, container, *args, **kwargs):
        super().__init__(handlers, *args, **kwargs)
        self.container = container


class CoreApiContainer(CoreBase):
    """
    The :class:`CoreApp` class is a facade for tornado's ``Application`` class.

    """

    enabled = True
    root = None
    max_workers = 10
    rules = []

    def __init__(self, handlers=None, **kwargs):
        CoreBase.__init__(self)
        for attr in ("debug", "compress_response", "websocket_ping_interval",
                     "websocket_ping_timeout", "cookie_secret"):
            kwargs[attr] = kwargs.get(attr, self.config.api.setting[attr])
        kwargs["default_handler_class"] = DefaultHandler
        kwargs["default_handler_args"] = ()
        kwargs["login_url"] = LOGIN_URL
        kwargs["log_function"] = self._log
        self._settings = kwargs
        self._rules = handlers or kwargs.get("handlers", [])
        self._pool = None

    def _log(self, handler):
        if handler.get_status() < 400:
            meth = self.logger.info
        elif handler.get_status() < 500:
            meth = self.logger.warning
        else:
            meth = self.logger.error
        request_time = 1000.0 * handler.request.request_time()
        meth("[%d] [%s %s] in [%.2fms] by [%s]",
             handler.get_status(), handler.request.method,
             handler.request.path, request_time, handler.current_user,
             extra={"identifier": handler.identifier})

    @property
    def executor(self):
        if self._pool is None:
            self.logger.info("initialised thread pool with [%d] workers",
                             self.max_workers)
            self._pool = ThreadPoolExecutor(max_workers=self.max_workers)
        return self._pool

    def get_root(self):
        root = self.root
        if root is None:
            root = self.project
        if not root.startswith("/"):
            root = "/" + root
        if root.endswith("/"):
            root = root[:-1]
        return root

    def make_application(self):
        rules = []
        for rule in self._rules + self.rules:
            if isinstance(rule, (tuple, list)):
                if len(rule) >= 2:
                    if isinstance(rule[0], str):
                        match = self.get_root() + rule[0]
                        self.logger.info("starting [%s] at [%s]",
                                         rule[1].__name__, match)
                        rules.append(
                            tornado.routing.Rule(
                                tornado.routing.PathMatches(match),
                                *rule[1:]))
                        continue
            raise core4.error.Core4SetupError(
                "routing requires list of tuples "
                "(str, handler)")
        app = CoreApplication(rules, self, **self._settings)
        # app.core_app = self
        return app


class CoreApiServerTool(core4.base.main.CoreBase,
                        core4.logger.mixin.CoreLoggerMixin):

    def make_routes(self, *args, **kwargs):
        routes = []
        roots = set()
        for container_cls in args:
            container_obj = container_cls(**kwargs)
            root = container_obj.get_root()
            if root in roots:
                raise core4.error.Core4SetupError(
                    "routing root [{}] duplicate".format(root)
                )
            tornado_app = container_obj.make_application()
            routes.append(
                tornado.routing.Rule(tornado.routing.PathMatches(
                    root + ".*"), tornado_app)
            )
            roots.add(root)
        return tornado.routing.RuleRouter(routes)

    def serve(self, *args, port=None, **kwargs):
        self.setup_logging()
        router = self.make_routes(*args, **kwargs)
        server = tornado.httpserver.HTTPServer(router)
        port = port or self.config.api.port
        server.listen(port)
        self.logger.info("open socket on port [%d]", port)
        tornado.ioloop.IOLoop.current().start()


def serve(*args, **kwargs):
    setup = core4.service.setup.CoreSetup()
    setup.make_role()
    CoreApiServerTool().serve(*args, **kwargs)
