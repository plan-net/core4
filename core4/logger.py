# -*- coding: utf-8 -*-

import logging
import time
import os
import logging.config
from core4.error import Core4SetupError
from core4.config.main import DEFAULT_CONFIG
import oyaml
import datetime
import core4.logger
import time
from bson.objectid import ObjectId


CORE4_PREFIX = "core4"
ACCOUNT_PREFIX = "account"

logging.Formatter.converter = time.gmtime


class CustomAdapter(logging.LoggerAdapter):
    """
    This example adapter expects the passed in dict-like object to have a
    'connid' key, whose value in brackets is prepended to the log message.
    """
    def process(self, msg, kwargs):
        kwargs["extra"] = self.extra
        kwargs['extra']['_id'] = ObjectId()
        return msg, kwargs


# see https://fangpenlin.com/posts/2012/08/26/good-logging-practice-in-python/


class MongoLoggingHandler(logging.Handler):
    """
    This class implements mongo logging initialised with a
    :class:`core.main.CoreCollection` defined by settings as delivered by
    :meth:`core.config.get_collection()` method.
    """

    def __init__(self, connection):
        super(MongoLoggingHandler, self).__init__()
        self._collection = connection

    def handle(self, record):
        ts = time.gmtime(record.created)
        doc = {}
        doc['created'] = datetime.datetime(ts.tm_year, ts.tm_mon, ts.tm_mday,
                                           ts.tm_hour, ts.tm_min, ts.tm_sec)
        for attr in ["message", "username", "identifier", "hostname",
                     "qual_name", "_id"]:
            doc[attr] = record.__dict__.get(attr, None)
        doc['level'] = record.levelname
        self._collection.insert_one(doc)


class CoreLoggerMixin:

    completed = False

    def setup_logging(self):
        if self.completed:
            return
        logger = logging.getLogger(CORE4_PREFIX)
        self._shutdown_logging(logger)
        logger.setLevel(logging.DEBUG)
        self._setup_console(logger)
        self._setup_mongodb(logger)
        self._setup_extra_logging(logger)
        self.logger.debug("logging setup complete")
        CoreLoggerMixin.completed = True

    def _shutdown_logging(self, logger):
        logger.handlers = []

    def _setup_console(self, logger):
        log_format = self.config.get('format', 'logging')
        for name in ("stdout", "stderr"):
            level = self.config.get(name, "logging")
            if level:
                handler = logging.StreamHandler()
                handler.setLevel(getattr(logging, level))
                formatter = logging.Formatter(log_format)
                handler.setFormatter(formatter)
                logger.addHandler(handler)
                self.logger.debug(
                    "{} logging setup complete, level {}".format(name, level))

    def _setup_mongodb(self, logger):
        mongodb = self.config.get("mongodb", "logging")
        if mongodb:
            conn = self.config.get_collection('sys.log', 'kernel')
            handler = MongoLoggingHandler(conn)
            handler.setLevel(getattr(logging, mongodb))
            logger.addHandler(handler)
            self.logger.debug(
                "mongodb logging setup complete, level {}".format(mongodb))

    def _setup_extra_logging(self, logger):
        config = self.config.get("config", "logging")
        if config:
            fullname = os.path.join(os.path.dirname(DEFAULT_CONFIG), config)
            if not os.path.exists(fullname):
                raise Core4SetupError("file {} not found".format(fullname))
            with open(fullname, 'rt') as f:
                config = oyaml.safe_load(f.read())
            if config:
                logging.config.dictConfig(config)
                self.logger.debug(
                    "extra logging setup complete from {}".format(fullname))
