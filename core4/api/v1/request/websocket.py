"""
Delivers the base class for web sockets with core4.
"""
import re

from tornado.websocket import WebSocketHandler

from core4.api.v1.request.main import CoreRequestHandler


class CoreWebSocketHandler(WebSocketHandler, CoreRequestHandler):
    """
    The :class:`.CoreWebSocketHandler` mixes :mod:`tornado`
    :class:`WebSocketHandler <tornado.websocket.WebSocketHandler>` with
    :class:`.CoreRequestHandler` features.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        origin = self.config.api.allow_origin.replace("*", ".*")
        self._check_origin = re.compile(origin)

    def check_origin(self, origin):
        """
        Applies CORS origin validation with core4 configuration setting
        ``api.allow_origin``
        """
        if self._check_origin.match(origin) is not None:
            allow = True
            self.logger.debug("accept origin [%s]", origin)
        else:
            self.logger.warning("deny origin [%s]", origin)
            allow = False
        return allow
