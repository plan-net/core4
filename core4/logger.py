# -*- coding: utf-8 -*-

import logging
import time
import os
import logging.config
from core4.error import Core4SetupError
from core4.config.main import DEFAULT_CONFIG
import oyaml


CORE4_PREFIX = "core4"
ACCOUNT_PREFIX = "account"


# see https://fangpenlin.com/posts/2012/08/26/good-logging-practice-in-python/


class UTCFormatter(logging.Formatter):
    converter = time.gmtime


class CoreLoggerMixin:

    def setup_logging(self):
        core_logger = logging.getLogger(CORE4_PREFIX)
        core_logger.setLevel(logging.DEBUG)
        self._setup_console(core_logger)
        self._setup_mongodb(core_logger)
        self._setup_extra_logging(core_logger)
        self.logger.debug("logging setup complete")

    def _setup_console(self, logger):
        # console logging setup
        log_format = self.config.get('format', 'logging')
        for name in ("stdout", "stderr"):
            level = self.config.get(name, "logging")
            if level:
                handler = logging.StreamHandler()
                handler.setLevel(getattr(logging, level))
                formatter = UTCFormatter(log_format)
                handler.setFormatter(formatter)
                logger.addHandler(handler)
                self.logger.debug(
                    "{} logging setup complete, level {}".format(name, level))

    def _setup_mongodb(self, logger):
        # mongodb logging setup
        mongodb = self.config.get("mongodb", "logging")
        if mongodb:
            pass

    def _setup_extra_logging(self, logger):
        # extra logging configuration
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
