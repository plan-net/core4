# -*- coding: utf-8 -*-

import logging
import time


CORE4_PREFIX = "core4"
ACCOUNT_PREFIX = "account"


class UTCFormatter(logging.Formatter):
    converter = time.gmtime


class CoreLoggerMixin:

    def start_logging(self):
        core_logger = logging.getLogger(CORE4_PREFIX)
        core_logger.setLevel(logging.DEBUG)
        # console logging setup
        console_handler = logging.StreamHandler()
        log_level = self.config.get('console_log_level', 'logging')
        console_handler.setLevel(getattr(logging, log_level))
        log_format = self.config.get('console_log_format', 'logging')
        formatter = UTCFormatter(log_format)
        console_handler.setFormatter(formatter)
        core_logger.addHandler(console_handler)
