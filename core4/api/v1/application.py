#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
This module implements :class:`.CoreApiContainer` bundling multiple request
handlers under the same root endpoint. This class uses
:class:`.CoreApplication` derived from :class:`tornado.web.Application` and a
hierarchical routing mechanic to deliver these endpoints.

A blueprint for server definition and startup is::

    from core4.api.v1.application import CoreApiContainer
    from core4.api.v1.request.queue.job import JobHandler
    from core4.api.v1.tool.functool import serve

    class TestContainer(CoreApiContainer):
        root = "/test/api"
        rules = [
            (r'/job/?(.*)', JobHandler)
        ]


    if __name__ == '__main__':
        serve(TestContainer)


Please note that :meth:`.serve` can handle one or multiple
:class:`.CoreApiContainner` objects with multiple endpoints and resources as in
the following example::

    serve(TestContainer, AnotherContainer)
"""

import hashlib
from pprint import pformat

import tornado.routing
import tornado.web

import core4.const
import core4.error
import core4.util.node
from core4.api.v1.request.default import DefaultHandler
from core4.api.v1.request.standard.info import InfoHandler
from core4.api.v1.request.kill import KillHandler
from core4.api.v1.request.main import CoreBaseHandler
from core4.api.v1.request.static import CoreStaticFileHandler
from core4.api.v1.request.standard.asset import CoreAssetHandler
from core4.base.main import CoreBase

STATIC_PATTERN = "/(.*)$"


class CoreRoutingRule(tornado.routing.Rule):
    """
    Routing rule inherited from :class:`tornado.routing.Rule. Adds the
    rule attribute ``.rsc_id`` which is used by core4 to uniquely identify
    resource handlers.
    """

    def __init__(self, rsc_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rsc_id = rsc_id


class CoreApiContainer(CoreBase):
    """
    :class:`CoreApiContainer` class is a container for a single or multiple
    :class:`.CoreRequestHandler`, :class.`.CoreStaticFilehandler` or
    :class:`.CoreWebSocketHandler`. It is based on the appropriate torando
    classes. a container encapsulates endpoint resources under the same
    :attr:`.root` URL prefix.

    The default ``root`` is equal to the project name.
    """

    #: if ``True`` then the application container is deployed with serve_all
    enabled = True
    #: root URL, defaults to the project name
    root = None
    #: list of tuples with route, request handler (i.e.
    #  :class:`.CoreRequestHandler` or class:`tornado.web.RequestHandler`
    #  derived class
    rules = []

    upwind = ["log_level", "enabled", "root"]

    def __init__(self, **kwargs):
        CoreBase.__init__(self)
        for attr in ("debug", "compress_response", "cookie_secret"):
            kwargs[attr] = kwargs.get(attr, self.config.api.setting[attr])
        kwargs["default_handler_class"] = DefaultHandler
        kwargs["default_handler_args"] = ()
        kwargs["log_function"] = self._log
        self._settings = kwargs
        self.started = None
        # upwind class properties from configuration
        for prop in ("enabled", "root"):
            if prop in self.class_config:
                if self.class_config[prop] is not None:
                    setattr(self, prop, self.class_config[prop])

    def _log(self, handler):
        # internal logging method
        if getattr(handler, "logger", None) is None:
            # regular logging
            logger = self.logger
            identifier = self.identifier
        else:
            # CoreRequestHandler logging
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

    def get_root(self, path=None):
        """
        Returns the container`s ``root`` URL prefix or prefixes the passed
        relative path with the prefix.

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
        """
        Returns a :class:`tornado.web.URLSpec` as specified by the container's
        :attr:`rules` attribute. This rules attribute can either be an
        ``URLSpec`` by itself or a tuple of ``pattern``, ``handler`` class,
        an optional ``kwargs`` to be passed to the handler and an optional
        rule ``name``.

        Additionally the following default handlers are added:

        * ``/_info`` to deliver the collection of available endpoints, the
          resources' card, help and enter UrL
        * ``/_asset`` to deliver assets
        * ``/_kill`` to kill the server

        :return: yields :class:`tornado.web.URLSpec` objects
        """
        yield tornado.web.URLSpec(
            pattern=self.get_root(core4.const.INFO_URL),
            handler=InfoHandler,
            kwargs=None,
            name=None
        )
        yield tornado.web.URLSpec(
            pattern=self.get_root(core4.const.KILL_URL),
            handler=KillHandler,
            kwargs=None,
            name=None
        )
        yield tornado.web.URLSpec(
            pattern=self.get_root("/{}/(default|project)/(.+?)/(.*)".format(
                core4.const.ASSET_URL)),
            handler=CoreAssetHandler,
            kwargs=None,
            name=None
        )
        for ret in self.rules:
            if isinstance(ret, tornado.web.URLSpec):
                pattern = self.get_root(ret.regex.pattern)
                handler = ret.target
                kwargs = ret.kwargs
                name = ret.name
            else:
                ret = list(ret)
                pattern = self.get_root(ret.pop(0))
                handler = ret.pop(0)
                if not issubclass(handler, tornado.web.RequestHandler):
                    raise core4.error.Core4SetupError(
                        "expected subclass of RequestHandler, not [{}]".format(
                            type(handler)
                        )
                    )
                try:
                    kwargs = ret.pop(0)
                except IndexError:
                    kwargs = None
                try:
                    name = ret.pop(0)
                except IndexError:
                    name = None
            if pattern.endswith("/"):
                pattern = pattern[:-1]
            if issubclass(handler, CoreStaticFileHandler):
                if kwargs is None:
                    kwargs = {}
                kwargs["enter"] = pattern
                yield tornado.web.URLSpec(
                    pattern= pattern + "/(.*)$",
                    handler=handler,
                    kwargs=kwargs,
                    name=name
                )
                yield tornado.web.URLSpec(
                    pattern=pattern + "(?:/(.*))?$",
                    handler=handler,
                    kwargs=kwargs,
                )
            else:
                yield tornado.web.URLSpec(
                    pattern=pattern,
                    handler=handler,
                    kwargs=kwargs,
                    name=name
                )

    def make_application(self):
        """
        Validates and pre-processes :class:`CoreApiContainer` rules and
        transfers a handler lookup dictionary to :class:`CoreApiServerTool`
        for reverse URL lookup.

        :return: :class:`.CoreApplication` instance
        """
        unique = set()
        rules = []
        for rule in self.iter_rule():
            routing = rule.regex.pattern
            cls = rule.target
            if rule.kwargs is None:
                kwargs = {}
            else:
                kwargs = rule.kwargs.copy()
            sorted_kwargs = pformat(kwargs)
            if issubclass(cls, CoreBaseHandler):
                qn = cls.qual_name()
            else:
                qn = ".".join([cls.__module__, cls.__name__])
            hash_base = " ".join([qn, sorted_kwargs])
            rsc_id = hashlib.md5(hash_base.encode("utf-8")).hexdigest()
            kwargs["_rsc_id"] = rsc_id
            if routing not in unique:
                unique.add(routing)
                rules.append(
                    CoreRoutingRule(
                        rsc_id,
                        tornado.routing.PathMatches(routing),
                        target=cls, target_kwargs=kwargs, name=rule.name))
                if issubclass(cls, CoreBaseHandler):
                    self.logger.debug(
                        "started [%s] on [%s] as [%s] with [%s]",
                        rule.target.qual_name(),
                        rule.regex.pattern,
                        rule.name or rsc_id, kwargs)
            else:
                raise core4.error.Core4SetupError(
                    "route [%s] already exists" % routing)
        app = CoreApplication(rules, self, **self._settings)
        self.started = core4.util.node.now()
        return app


    def on_enter(self):
        """
        Overwrite this method for code to be executed when the container enters
        the io loop.
        """
        pass

    def on_exit(self):
        """
        Overwrite this method for code to be executed when the container exits
        the io loop.
        """
        pass


class CoreApplication(tornado.web.Application):
    """
    Represents a wrapper class around :class:`tornado.web.Application`. This
    wrapper extends applications' properties with a ``.container`` property
    referencing the :class:`.CoreApiContainer` object and delivers special
    processing for the *CARD* and *ENTER* handler requests.
    """

    def __init__(self, handlers, container, *args, **kwargs):
        super().__init__(handlers, *args, **kwargs)
        self.container = container
        self.identifier = container.identifier
        self.lookup = {}
        for handler in handlers:
            self.lookup.setdefault(handler.rsc_id, {
                "handler": handler,
                "pattern": []
            })["pattern"].append({
                "regex": handler.matcher.regex.pattern,
                "name": handler.name
            })

    def find_handler(self, request, **kwargs):
        """
        Implements special handling for card page requests and landing page
        requests (*ENTER*).

        Card page requests are forwarded to the handler's
        :meth:`.CoreRequestHandler.card` method (``XCARD``). Enter landing
        page requests are forwarded to the handler's
        :meth:`.CoreRequestHandler.enter` method (``XENTER``).
        """
        if request.path.startswith(self.container.get_root(
                core4.const.INFO_URL)):
            root = self.container.get_root(core4.const.INFO_URL)
            split = request.path[len(root) + 1:].split("/")
            if len(split) == 2:
                mode = split[0]
                handler = self.lookup[split[1]]["handler"]
                if mode == core4.const.CARD_MODE:
                    request.method = core4.const.CARD_METHOD
                    return self.get_handler_delegate(request, handler.target,
                                                     handler.target_kwargs)
                elif mode == core4.const.ENTER_MODE:
                    request.method = core4.const.ENTER_METHOD
                    return self.get_handler_delegate(request, handler.target,
                                                     handler.target_kwargs)
                elif mode == core4.const.HELP_MODE:
                    request.method = core4.const.HELP_METHOD
                    return self.get_handler_delegate(request, handler.target,
                                                     handler.target_kwargs)
        return super().find_handler(request, **kwargs)

    def handler_help(self, cls):
        """
        Delivers dict with help information about the passed
        :class:`.CoreRequestHandler` class

        :param cls: :class:`.CoreRequestHandler` class
        :return: dict as delivered by :meth:`.CoreApiInspectir.handler_info`
        """
        from core4.service.introspect.api import CoreApiInspector
        inspect = core4.service.introspect.api.CoreApiInspector()
        return inspect.handler_info(cls)
