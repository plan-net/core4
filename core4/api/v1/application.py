"""
This module delivers the :class:`.CoreApplication` derived from
:class:`tornado.web.Application`, :class:`.CoreApiContainer` encapsulating
one or more applications and a helper method :meth:`serve` utilising
:class:`.CoreApiServerTool` for server and endpoint management.

A blueprint for server definition and startup is::

    from core4.api.v1.application import CoreApiContainer, serve
    from core4.api.v1.request.queue.job import JobHandler

    class CoreApiServer(CoreApiContainer):
        root = "core4/api/v1"
        rules = [
            (r'/job/?(.*)', JobHandler)
        ]


    if __name__ == '__main__':
        serve(CoreApiServer)


Please note that :meth:`serve` can handle one or multiple
:class:`.CoreApiServer` objects with multiple endpoints and resources as in
the following example::

    serve(CoreApiServer, CoreAnotherpiAServer)
"""

from concurrent.futures import ThreadPoolExecutor

import tornado.routing
import tornado.web

import core4.error
import core4.util.node
from core4.logger.mixin import CoreLoggerMixin
import core4.service.setup
from core4.api.v1.request.default import DefaultHandler
from core4.api.v1.request.standard.login import LoginHandler
from core4.api.v1.request.standard.logout import LogoutHandler
from core4.api.v1.request.standard.profile import ProfileHandler
from core4.api.v1.request.static import CoreStaticFileHandler
from core4.base.main import CoreBase
import core4.util


class CoreApiContainer(CoreBase):
    """
    The :class:`CoreApiContainer` class is a container for tornado's
    ``Application`` objects. The container encapsulates endpoint resources
    under the same :attr:`.root` URL defined by the :attr:`.root` attribute.
    """

    #: if ``True`` then the application container is autmatically deployed
    enabled = True
    #: root URL, defaults to the project name
    root = None
    #: list of tuples with route and :class:`.CoreRequestHandler`
    rules = []
    #: path to static files
    path = None
    #: default static filename in a directory
    default_filename = "index.html"
    #: url attached to :attr:`.root` to serve static files
    static_url = 'static'
    #: number of executor threads/processes (experimental)
    max_workers = 10

    def __init__(self, handlers=None, **kwargs):
        CoreBase.__init__(self)
        for attr in ("debug", "compress_response", "cookie_secret"):
            kwargs[attr] = kwargs.get(attr, self.config.api.setting[attr])
            #self.logger.critical("have %s = %s", attr, kwargs[attr])
        self._rules = handlers or kwargs.get("handlers", [])
        self._pool = None
        self.default_routes = [
            ("/login", LoginHandler),
            ("/logout", LogoutHandler),
            ("/profile", ProfileHandler),
        ]
        # kwargs["login_url"] = self.get_root() + "/login"
        kwargs["default_handler_class"] = DefaultHandler
        kwargs["default_handler_args"] = ()
        kwargs["log_function"] = self._log
        if self.path:
            kwargs["static_path"] = self.path
            if self.default_filename:
                kwargs["default_filename"] = self.default_filename
            if self.static_url:
                kwargs["static_url_prefix"] = self.get_root(self.static_url)
                if not kwargs["static_url_prefix"].endswith("/"):
                    kwargs["static_url_prefix"] += "/"
                if not kwargs["static_url_prefix"].startswith("/"):
                    kwargs["static_url_prefix"] = kwargs[
                                                      "static_url_prefix"][1:]
            kwargs["static_handler_class"] = CoreStaticFileHandler
        self._settings = kwargs

    def _log(self, handler):
        # internal logging method
        if handler.get_status() < 400:
            meth = handler.logger.info
        elif handler.get_status() < 500:
            meth = handler.logger.warning
        else:
            meth = handler.logger.error
        request_time = 1000.0 * handler.request.request_time()
        meth("[%d] [%s %s] in [%.2fms] by [%s] from [%s]",
             handler.get_status(), handler.request.method,
             handler.request.path, request_time, handler.current_user,
             self.identifier, extra={"identifier": handler.identifier})

    def get_root(self, path=None):
        """
        Returns the container`s ``root`` URL or prefixes the passed relative
        path with the container's ``root``

        :param path: relative path (optional)
        :return: ``root`` or absolute path below ``root``
        """
        root = self.root
        if root is None:
            root = self.project
        if not root.startswith("/"):
            root = "/" + root
        if root.endswith("/"):
            root = root[:-1]
        if path:
            if not path.startswith("/"):
                path = "/" + path
            return root + path
        return root

    def make_application(self):
        """
        Parses the :class:`CoreApiContainer` objects' rules, attached the
        :attr:`.root` url and creates the :class:`.CoreApplication` objects
        passing the settings from :meth:`serve`.

        :return: :class:`.CoreApplication` instance
        """
        rules = []
        roots = set()
        self.logger.info("startup [%s]", self.get_root())
        for rule in self.default_routes + self._rules + self.rules:
            if isinstance(rule, (tuple, list)):
                if len(rule) >= 2:
                    if isinstance(rule[0], str):
                        match = self.get_root(rule[0])
                        if not match in roots:
                            self.logger.info("starting [%s] with [%s]",
                                             match, rule[1].__name__)
                            roots.add(match)
                            rules.append(
                                tornado.routing.Rule(
                                    tornado.routing.PathMatches(match),
                                    *rule[1:]))
                        else:
                            self.logger.warning("route [%s] already exists",
                                                match)
                        continue
            raise core4.error.Core4SetupError(
                "routing requires list of tuples "
                "(str, handler)")
        app = CoreApplication(rules, self, **self._settings)
        return app

    @property
    def executor(self):
        if self._pool is None:
            self.logger.info("initialised thread pool with [%d] workers",
                             self.max_workers)
            self._pool = ThreadPoolExecutor(max_workers=self.max_workers)
        return self._pool


class CoreApplication(tornado.web.Application):
    """
    Represents a wrapper class around :class:`tornado.web.Application`. This
    wrapper extends applications' properties with a ``.container`` property
    referencing the :class:`.CoreApiContainer` object.
    """

    def __init__(self, handlers, container, *args, **kwargs):
        super().__init__(handlers, *args, **kwargs)
        self.container = container
        self.identifier = container.identifier


class CoreApiServerTool(CoreBase, CoreLoggerMixin):
    """
    Helper class to :meth:`serve` :class:`CoreApiContainer` classes.
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

    def serve(self, *args, port=None, name=None, **kwargs):
        """
        Starts the tornado HTTP server listening on the specified port and
        enters tornado's IOLoop.

        :param args: one or more :class:`CoreApiContainer` classes
        :param port: to listen, defaults to ``5001``, see core4 configuration
                     setting ``api.port``
        :param name: to identify the server
        :param kwargs: to be passed to all :class:`CoreApiApplication`
        """
        self.identifier = name or core4.util.node.get_hostname()
        self.setup_logging()
        router = self.make_routes(*args, **kwargs)
        http_args = {}
        cert_file = self.config.api.crt_file
        key_file = self.config.api.key_file
        if cert_file and key_file:
            self.logger.info("securing server with [%s]", cert_file)
            http_args["ssl_options"] = {
                "certfile": cert_file,
                "keyfile": key_file,
            }
        server = tornado.httpserver.HTTPServer(
            router, **http_args)
        port = port or self.config.api.port
        server.listen(port)
        self.logger.info(
            "open %ssecure socket on port [%d]",
            "" if http_args.get("ssl_options") else "NOT ", port)
        tornado.ioloop.IOLoop.current().start()


def serve(*args, port=None, name=None, **kwargs):
    """
    Setup core4 environment (using :class:`.CoreSetup`) and serve one or
    multiple :class:`.CoreApiContainer` classes.

    Additional keyword arguments are passed to the
    :class:`tornado.web.Application` object. Good to know keyword arguments
    with their default values from core4 configuration section ``api.setting``
    are::

    * ``debug`` - defaults to ``True``
    * ``compress_response`` - defaults to ``True``
    * ``cookie_secret`` - no default defined

    .. warning:: core4 configuration setting ``cookie_secret`` does not provide
                 any defaults and must be set.

    Additionally the following core4 config settings specify the tornado
    application:

    * ``crt_file`` and ``key_file`` for SSL support, if these settings are
      ``None``, then SSL support is disabled
    * ``allow_origin`` - server pattern to allow CORS (cross-origin resource
      sharing)
    * ``port`` - default port (5001)
    * ``error_html_page`` - default error page with content type ``text/html``
    * ``error_text_page`` - default error page with content tpe ``text/plain``

    Each :class:`.CoreApiContainer` is defined by a unique ``root`` URL. This
    ``root`` URL defaults to the project name and is specified in the
    :class:`.CoreApiContainer` class. The container delivers the following
    default endpoints under it's ``root``:

    * ``/login`` serving
      :class:`core4.api.v1.request.standard.login.LoginHandler`
    * ``/logout`` serving
      :class:`core4.api.v1.request.standard.logout.LogoutHandler`
    * ``/profile`` serving
      :class:`core4.api.v1.request.standard.profile.ProfileHandler`

    .. note:: This method creates the required core4 environment including
              the standard core4 folders (see config setting ``folder``,
              the default users and roles (see config setting
              ``admin_username``, ``admin_realname`` and ``admin_password``.

    :param args: class dervived from :class:`.CoreApiContainer`
    :param port: to serve, defaults to core4 config ``api.port``
    :param name: to identify the server, defaults to hostname
    :param kwargs: passed to the :class:`tornado.web.Application` objects
    """
    setup = core4.service.setup.CoreSetup()
    setup.make_all()
    CoreApiServerTool().serve(*args, port=port, name=name, **kwargs)
