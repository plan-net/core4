import logging.config
from bson.objectid import ObjectId
import logging.config

from bson.objectid import ObjectId


class CoreLoggingAdapter(logging.LoggerAdapter):
    """
    This adapter passes all extra key/value pairs and creates an
    ``_id`` of type :class:`.ObjectId`.
    """

    def process(self, msg, kwargs):
        kwargs["extra"] = {
            "obj": self.extra,
            "_id": ObjectId()
        }
        return msg, kwargs


