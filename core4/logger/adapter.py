import logging.config


class CoreLoggingAdapter(logging.LoggerAdapter):
    """
    This adapter passes the object to logging.
    """

    def process(self, msg, kwargs):
        kwargs["extra"] = {
            "obj": self.extra,
        }
        return msg, kwargs
