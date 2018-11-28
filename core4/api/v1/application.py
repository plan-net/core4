"""
This module delivers the :class:`.CoreApplication` derived from
:class:`tornado.web.Application`, :class:`.CoreApiContainer` encapsulating
one or more applications and a helper method :meth:`.serve` utilising
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


Please note that :meth:`.serve` can handle one or multiple
:class:`.CoreApiServer` objects with multiple endpoints and resources as in
the following example::

    serve(CoreApiServer, CoreAnotherpiAServer)
"""

# import tornado.escape
import base64

import tornado.routing
import tornado.routing
import tornado.web
import tornado.web

import core4.error
import core4.service.setup
import core4.util
import core4.util.node
from core4.api.v1.request.default import DefaultHandler
from core4.api.v1.request.standard.login import LoginHandler
from core4.api.v1.request.standard.logout import LogoutHandler
from core4.api.v1.request.standard.profile import ProfileHandler
from core4.base.main import CoreBase

# import tornado.escape

XCARD = "/_xcard_"
XCOLL = "/_xcoll_"


class CoreApiContainer(CoreBase):
    """
    The :class:`CoreApiContainer` class is a container for tornado's
    ``Application`` objects. The container encapsulates endpoint resources
    under the same :attr:`.root` URL defined by the :attr:`.root` attribute.

    The default ``root`` is the project name.
    """

    #: if ``True`` then the application container is autmatically deployed
    enabled = True
    #: root URL, defaults to the project name
    root = None
    #: list of tuples with route and :class:`.CoreRequestHandler`
    rules = []
    upwind = ["log_level", "enabled", "root"]

    def __init__(self, handlers=None, **kwargs):
        CoreBase.__init__(self)
        for attr in ("debug", "compress_response", "cookie_secret"):
            kwargs[attr] = kwargs.get(attr, self.config.api.setting[attr])
            # self.logger.debug("have %s = %s", attr, kwargs[attr])
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
        self._settings = kwargs
        # upwind class properties from configuration
        for prop in ("enabled", "root"):
            if prop in self.class_config:
                if self.class_config[prop] is not None:
                    setattr(self, prop, self.class_config[prop])
        self.rule_lookup = {}

    def _log(self, handler):
        # internal logging method
        if getattr(handler, "logger", None) is None:
            logger = self.logger
            identifier = self.identifier
        else:
            logger = handler.logger
            identifier = handler.identifier
        if handler.get_status() < 400:
            meth = logger.info
        elif handler.get_status() < 500:
            meth = logger.warning
        else:
            meth = logger.error
        request_time = 1000.0 * handler.request.request_time()
        meth("[%d] [%s %s] in [%.2fms] by [%s] from [%s]",
             handler.get_status(), handler.request.method,
             handler.request.path, request_time, handler.current_user,
             self.identifier, extra={"identifier": identifier})

    @classmethod
    def url(cls, *args):
        """
        Class method to prefix the passed, optional URL with the ``root`` using
        :meth:`.get_root`.

        :param args: optional URL str
        :return: absolute path
        """
        return cls().get_root(*args)

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

    def iter_rule(self):
        for rule in self.default_routes + self._rules + self.rules:
            ret = list(rule[:])
            ret[0] = self.get_root(ret[0])
            yield ret

    def make_application(self):
        """
        Parses the :class:`CoreApiContainer` objects' rules, attached the
        :attr:`.root` url and creates the :class:`.CoreApplication` objects
        passing the settings from :meth:`.serve`.

        :return: :class:`.CoreApplication` instance
        """
        rules = []
        roots = set()
        for rule in self.iter_rule():
            if isinstance(rule, (tuple, list)):
                if len(rule) >= 2:
                    routing = rule[0]
                    cls = rule[1]
                    if isinstance(routing, str):
                        if routing not in roots:
                            rule_name = base64.b16encode(
                                bytes(routing, encoding="utf-8")).decode()
                            self.logger.info("starting [%s] with [%s]",
                                             routing, cls.__name__)
                            roots.add(routing)
                            rules.append(
                                tornado.routing.Rule(
                                    tornado.routing.PathMatches(routing),
                                    *rule[1:], name=rule_name))
                            self.rule_lookup[rule_name] = rule[1:]
                        else:
                            self.logger.error("route [%s] already exists",
                                              routing)
                        continue
            raise core4.error.Core4SetupError(
                "routing requires list of tuples "
                "(str, handler)")
        return CoreApplication(rules, self, **self._settings)


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
        get_root = getattr(self.container, "get_root", None)
        if get_root:
            self.root = get_root()
        else:
            self.root = None

    def find_handler(self, request, **kwargs):
        if request.path == self.root:
            if "_xcard" in request.query_arguments:
                cls = self.container.rule_lookup[
                    request.query_arguments["_xcard"][0].decode("utf-8")]
                request.method = "XCARD"
                return self.get_handler_delegate(request, *cls)
            # return self.get_handler_delegate(
            #     request,
            #     self.settings['default_handler_class'],
            #     self.settings.get('default_handler_args', {}))
        return super().find_handler(request, **kwargs)
