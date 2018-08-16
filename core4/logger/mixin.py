# -*- coding: utf-8 -*-

import logging
import logging.config
import time

import core4.error
import core4.logger
import core4.logger.exception
import core4.logger.handler
import core4.util

logging.Formatter.converter = time.gmtime  # log in UTC


class CoreLoggerMixin:

    """
    If your application wants to enable logging, mixin
    :class:`.CoreLoggerMixin` and call :meth:`.setup_logging`. This will
    instantiate your logging needs as defined in core4 cascading configuration.
    """

    completed = False

    def setup_logging(self):
        """
        setup logging as specified in configuration. See :ref:`core_config`
        ``logging`` for further details.
        """
        if CoreLoggerMixin.completed:
            return
        logger = logging.getLogger(core4.logger.CORE4_PREFIX)
        self._shutdown_logging(logger)
        logger.setLevel(logging.DEBUG)
        self._setup_console(logger)
        self._setup_exception_logger(logger)
        self._setup_mongodb(logger)
        self._setup_extra_logging(logger)
        self.logger.debug("logging setup complete")
        CoreLoggerMixin.completed = True

    def _shutdown_logging(self, logger):
        logger.handlers = []

    def _setup_console(self, logger):
        log_format = self.config.logging.format
        for name in ("stdout", "stderr"):
            level = self.config.logging[name]
            if level:
                handler = logging.StreamHandler()
                handler.setLevel(getattr(logging, level))
                formatter = logging.Formatter(log_format)
                handler.setFormatter(formatter)
                logger.addHandler(handler)
                self.logger.debug(
                    "{} logging setup complete, level {}".format(name, level))

    def _setup_mongodb(self, logger):
        mongodb = self.config.logging.mongodb
        if mongodb:
            conn = self.config.sys.log
            if conn:
                handler = core4.logger.handler.MongoLoggingHandler(conn)
                handler.setLevel(getattr(logging, mongodb))
                logger.addHandler(handler)
                self.logger.debug(
                    "mongodb logging setup complete, level {}".format(mongodb))
            else:
                raise core4.error.Core4SetupError(
                    "config.logging.mongodb set, but config.sys.log is None")

    def _setup_extra_logging(self, logger):
        extra = self.config.logging.extra
        print(self.config)
        if extra:
            logging.config.dictConfig(extra)
            self.logger.debug("extra logging setup complete from")

    def _setup_exception_logger(self, logger):
        mongodb = self.config.logging.mongodb
        if mongodb:
            mongo_level = getattr(logging, mongodb)
            if mongo_level > logging.DEBUG:
                handler = core4.logger.exception.ExceptionHandler(
                    level=self.config.logging.mongodb,
                    size=self.config.logging.exception.capacity,
                    target=self.config.sys.log)
                handler.setLevel(logging.DEBUG)
                logger.addHandler(handler)
                self.logger.debug("exception logging setup complete")
            else:
                self.logger.warning(
                    "exception logging skipped "
                    "with mongodb loglevel [{}]".format(
                        self.config.logging.mongodb))
        else:
            self.logger.warning("exception logging disabled")
