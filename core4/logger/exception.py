#
#Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
#This Source Code Form is subject to the terms of the Mozilla Public
#License, v. 2.0. If a copy of the MPL was not distributed with this
#file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Implements :class:`CoreExceptionHandler` to stack and dump all low-level
exceptions in case a CRITICAL log level message occurs.
"""

import collections
import logging

from core4.logger.handler import make_record

FLUSH_LEVEL = logging.CRITICAL


class CoreExceptionHandler(logging.Handler):
    """
    This handler stacks all :attr:`logging.DEBUG` log records. If a log record
    with log level :attr:`logging.CRITICAL` appears, then all memorised log
    records are fed into ``sys.log`` MongoDB collection.
    """

    def __init__(self, *args, level, size, target, **kwargs):
        super().__init__(size, *args, **kwargs)
        self.mongo_level = getattr(logging, level)
        self.size = size
        self.target = target
        self.queue = None
        self.flush()

    def emit(self, record):
        """
        Emit a record and :meth:`.flush` if a log level of
        :attr:`logging.CRITICAL` or above appears.
        """
        if record.levelno < self.mongo_level:
            doc = make_record(record)
            self.queue.append(doc)
        if record.levelno >= FLUSH_LEVEL:
            self.acquire()
            try:
                if self.target:
                    for doc in self.queue:
                        self.target.insert_one(doc)
            finally:
                self.release()
                self.flush()

    def flush(self):
        """
        Truncates the buffer of log records
        """
        self.queue = collections.deque(maxlen=self.size)
