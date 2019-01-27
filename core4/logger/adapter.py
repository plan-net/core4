"""
Implements the logging adapter :class:`CoreLoggingAdapter`.
"""

import logging.config


class CoreLoggingAdapter(logging.LoggerAdapter):
    """
    This adapter passes the object to logging.
    """

    def process(self, msg, kwargs):
        kwargs.setdefault("extra", {}).update({"obj": self.extra})
        return msg, kwargs
