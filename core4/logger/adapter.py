import logging.config


class CoreLoggingAdapter(logging.LoggerAdapter):
    """
    This adapter passes the object and creates an ``_id`` of type
    :class:`bson.object.ObjectId`.
    """

    def process(self, msg, kwargs):
        kwargs["extra"] = {
            "obj": self.extra,
        }
        return msg, kwargs
