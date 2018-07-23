# -*- coding: utf-8 -*-

import logging
import logging.config
import os
import time

import datetime
import oyaml
from bson.objectid import ObjectId

from core4.config import DEFAULT_CONFIG
from core4.error import Core4SetupError

CORE4_PREFIX = "core4"  # top logger "core4"
ACCOUNT_PREFIX = "account"  # plugin logger beneath "core4.account"

logging.Formatter.converter = time.gmtime  # log in UTC


class CoreLoggingAdapter(logging.LoggerAdapter):
    """
    This adapter passes all extra key/value pairs and creates an
    ``_id`` of type :class:`.ObjectId`.
    """

    def process(self, msg, kwargs):
        kwargs["extra"] = self.extra
        kwargs['extra']['_id'] = ObjectId()
        return msg, kwargs


class MongoLoggingHandler(logging.Handler):
    """
    This class implements mongo logging.
    """

    def __init__(self, connection):
        """
        Connects the logging handler with the passed MongoDB connection.

        :param connection: :class:`pymongo.collection.Collection` object
        """
        super(MongoLoggingHandler, self).__init__()
        self._collection = connection

    def handle(self, record):
        """
        Handles the logging record by translating it into a mongo database
        document. The following attributes are saved for each
        :class:`logging.LogRecord`.

        * ``_id`` - the document id as created by
          :class:`core4.logger.MongoAdapter`
        * ``created`` - the logging datetime in UTC
        * ``level`` - the log level as string (``DEBUG``, ``INFO``, ``WARNING``,
          ``ERROR``, ``CRITICAL``)
        * ``hostname`` - the name of the host sending the message
        * ``user`` - the name of the user sending
        * ``qual_name`` - the qualified name of the class as created by
          :meth:`.CoreBase.qual_name`
        * ``identifier`` - the core object identifier; this identifier qualifies
          core workers with the worker name, core jobs with the worker and
          job id and API requests with its request id
        * ``message`` - the log message

        :param record: the log record (:class:`logging.LogRecord`)
        """
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
        """
        setup logging as specified in configuration. See configuration section
        ``logging`` for further details.
        """
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
