#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Implements :class:`CoreLoggerMixin` and :func:`logon` to switch on core4
logging, and :class:`CoreExceptionLoggerMixin` to enable a log dump if CRITICAL
log messages occur.
"""
import logging
import logging.config

import pymongo
import time

import core4.base
import core4.const
import core4.error
import core4.logger
import core4.logger.exception
import core4.logger.filter
import core4.logger.handler

logging.Formatter.converter = time.gmtime  # log in UTC


class CoreLoggerMixin:
    """
    If your application wants to enable logging, mixin
    :class:`.CoreLoggerMixin` and call :meth:`.setup_logging`.
    """

    completed = False

    def setup_logging(self):
        """
        setup logging as specified in configuration. See :ref:`core_config`
        ``logging`` for further details.
        """
        if not CoreLoggerMixin.completed:
            logger = logging.getLogger(core4.const.CORE4)
            logger.handlers = []  # logging shutdown
            logger.setLevel(logging.DEBUG)
            self._setup_console(logger)
            self._setup_mongodb(logger)
            self._setup_extra_logging(logger)
            self.logger.debug("logging setup complete")
            CoreLoggerMixin.completed = True

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
                self._setup_tornado(handler, level)
                self.logger.debug(
                    "{} logging setup complete, level {}".format(
                        name, level))

    def _setup_tornado(self, handler, level):
        for name in ("access", "application", "general"):
            logger = logging.getLogger("tornado." + name)
            logger.addHandler(handler)
            logger.setLevel(level)
            f = core4.logger.filter.CoreLoggingFilter()
            logger.addFilter(f)

    def _setup_mongodb(self, logger):
        mongodb = self.config.logging.mongodb
        if mongodb:
            conn = self.config.sys.log
            if conn:
                conn = conn.connect()
                existing = conn.connection[
                    conn.database].list_collection_names()
                if conn.collection not in existing:
                    try:
                        conn.connection[conn.database].create_collection(
                            name=conn.name,
                            capped=True,
                            size=self.config.logging.size
                        )
                        conn.create_index([("created", pymongo.DESCENDING)],
                                          name="created")
                    except:
                        self.logger.warning("failed to create [sys.log]")
                level = getattr(logging, mongodb)
                write_concern = self.config.logging.write_concern
                handler = core4.logger.handler.MongoLoggingHandler(
                    conn.with_options(write_concern=pymongo.WriteConcern(
                        w=write_concern
                    )))
                handler.setLevel(level)
                logger.addHandler(handler)
                self._setup_tornado(handler, level)
                self.logger.debug(
                    "mongodb logging setup complete, "
                    "level [%s], write concern [%d]", mongodb, write_concern)
            else:
                raise core4.error.Core4SetupError(
                    "config.logging.mongodb set, but config.sys.log is None")

    def _setup_extra_logging(self, logger):
        extra = self.config.logging.extra
        if extra:
            logging.config.dictConfig(extra)
            self.logger.debug("extra logging setup complete from")


class CoreExceptionLoggerMixin:
    """
    If your object wants exception logging, mixin
    :class:`.CoreExceptionLoggerMixin` and call :meth:`.add_exception_logger`.
    This bumps all log messages with level below the object`s standard log
    level if a ``CRITICAL`` log message occurs. See :ref:`exception_logging`.
    """

    def add_exception_logger(self):
        if not (hasattr(self, "config") and hasattr(self, "logger")):
            raise core4.error.Core4UsageError("method requires CoreBase class")
        mongodb = self.config.logging.mongodb
        if mongodb:
            mongo_level = getattr(logging, mongodb)
            if mongo_level > logging.DEBUG:
                handler = core4.logger.exception.CoreExceptionHandler(
                    level=self.config.logging.mongodb,
                    size=self.config.logging.exception.capacity,
                    target=self.config.sys.log)
                handler.setLevel(logging.DEBUG)
                logger = logging.getLogger(self.qual_name(short=False))
                logger.addHandler(handler)


def logon():
    """
    Helper method to turn on logging as defined in core4 configuration.
    """

    class Logger(core4.base.CoreBase, CoreLoggerMixin):
        pass

    Logger().setup_logging()
