"""
Helper tools :meth:`.serve`` and :meth:`.serve_all` with the underlying
:class:`.CoreApiServerTool`.
"""
import importlib

import tornado.httpserver
import tornado.routing

import core4.error
import core4.service.introspect
import core4.util.node
from core4.api.v1.application import RootContainer
from core4.base import CoreBase
from core4.logger import CoreLoggerMixin


class CoreApiServerTool(CoreBase, CoreLoggerMixin):
    """
    Helper class to :meth:`.serve` :class:`CoreApiContainer` classes.
    """

    def make_routes(self, protocol, port, address, *args, **kwargs):
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
            base_url = "%s://%s:%d" % (
                protocol, address or core4.util.node.get_hostname(), port
            )
            container_obj = container_cls(base_url=base_url, **kwargs)
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
            # self.register(
            #     container_obj, protocol, address, port, root
            # )
            application = container_obj.make_application()
            routes.append(
                tornado.routing.Rule(tornado.routing.PathMatches(
                    root + ".*"), application)
            )
            roots.add(root)
        return tornado.routing.RuleRouter(routes)

    def register(self, application, protocol, address, port, root):
        hostname = core4.util.node.get_hostname()
        url = "%s://%s:%d%s" % (protocol, address or hostname, port, root)
        now = core4.util.node.mongo_now()
        doc = {
            "url": url,
            "hostname": hostname,
            "protocol": protocol,
            "address": address,
            "port": port,
            "root": root,
            "container": application.qual_name()
        }
        self.config.sys.app.update_one(
            doc,
            update={
                "$setOnInsert": {
                    "created": now,
                },
                "$set": {
                    "updated": now
                }
            },
            upsert=True)
        self.logger.info("registered [%s]", url)

    def serve(self, *args, port=None, address=None, name=None, reuse_port=True,
              **kwargs):
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
        :param kwargs: to be passed to all :class:`CoreApiApplication`
        """
        self.identifier = name or core4.util.node.get_hostname()
        self.setup_logging()

        setup = core4.service.setup.CoreSetup()
        setup.make_all()

        http_args = {}
        cert_file = self.config.api.crt_file
        key_file = self.config.api.key_file
        proto = "http"
        if cert_file and key_file:
            self.logger.info("securing server with [%s]", cert_file)
            http_args["ssl_options"] = {
                "certfile": cert_file,
                "keyfile": key_file,
            }
            proto = "https"

        port = port or self.config.api.port
        self.router = self.make_routes(proto, port, address, *args, **kwargs)

        server = tornado.httpserver.HTTPServer(self.router, **http_args)
        server.bind(port, address=address, reuse_port=reuse_port)
        server.start()
        self.logger.info("open %ssecure socket on port [%d]",
                         "" if http_args.get("ssl_options") else "NOT ", port)
        try:
            tornado.ioloop.IOLoop().current().start()
        except KeyboardInterrupt:
            tornado.ioloop.IOLoop().current().stop()
            raise SystemExit()
        except:
            raise

    def serve_all(self, filter=None, port=None, address=None, name=None,
                  reuse_port=True, **kwargs):
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
        :param reuse_port: tells the kernel to reuse a local socket in
                           ``TIME_WAIT`` state, defaults to ``True``
        :param name: to identify the server
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
        self.serve(*clist, port=port, name=name, address=address,
                   reuse_port=reuse_port, **kwargs)


def serve(*args, port=None, address=None, name=None, reuse_port=True,
          **kwargs):
    """
    Serve one or multiple :class:`.CoreApiContainer` classes.

    Additional keyword arguments are passed to the
    :class:`tornado.web.Application` object. Good to know keyword arguments
    with their default values from core4 configuration section ``api.setting``
    are:

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
    :param address: IP address or hostname.  If it's a hostname, the server
                    will listen on all IP addresses associated with the name.
                    Address may be an empty string or None to listen on all
                    available interfaces.
    :param name: to identify the server, defaults to hostname
    :param reuse_port: tells the kernel to reuse a local socket in
                       ``TIME_WAIT`` state, defaults to ``True``
    :param kwargs: passed to the :class:`tornado.web.Application` objects
    """
    CoreApiServerTool().serve(*args, port=port, address=address, name=name,
                              reuse_port=reuse_port, **kwargs)


def serve_all(filter=None, port=None, address=None, name=None, reuse_port=True,
              **kwargs):
    """
    Serve all enabled core :class:`.CoreApiContainer` classes.

    To filter :class:`.CoreApiContainer` classes to be served use one or
    multiple  ``filter`` arguments. All :class:`.CoreApiContainer` with a
    :meth:`.qual_name <core4.base.main.CoreBase.qual_name>` starting with the
    provided filters will be in scope of API application serving.

    For other arguments see :meth:`serve`.

    :param filter: one or multiple str values to filter
                   :meth:`.qual_name <core4.base.main.CoreBase.qual_name>`
                   of the :class:`.CoreApiContainer` to be served.
    :param port: to serve, defaults to core4 config ``api.port``
    :param address: IP address or hostname.  If it's a hostname, the server
                    will listen on all IP addresses associated with the name.
                    Address may be an empty string or None to listen on all
                    available interfaces.
    :param name: to identify the server, defaults to hostname
    :param reuse_port: tells the kernel to reuse a local socket in
                       ``TIME_WAIT`` state, defaults to ``True``
    :param kwargs: passed to the :class:`tornado.web.Application` objects
    """
    CoreApiServerTool().serve_all(filter, port, address, name, reuse_port,
                                  **kwargs)


if __name__ == '__main__':
    # from core4.service.introspect import CoreIntrospector
    # intro = CoreIntrospector()
    # for pro in intro.iter_project():
    #     print(pro)
    serve_all(filter=["project.api",  # "core4",
                      "example"])  # , name=sys.argv[1], port=int(sys.argv[2]))
