# -*- coding: utf-8 -*-

import collections
import logging

import core4.logger.handler

FLUSH_LEVEL = logging.CRITICAL


class ExceptionHandler(logging.Handler):

    def __init__(self, *args, level, size, target, **kwargs):
        super().__init__(size, *args, **kwargs)
        self.mongo_level = getattr(logging, level)
        self.size = size
        self.target = target
        self.flush()

    def emit(self, record):
        """
        Emit a record.

        Append the record. If shouldFlush() tells us to, call flush() to process
        the buffer.
        """
        if record.levelno < self.mongo_level:
            doc = core4.logger.handler.make_record(record)
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

    # def close(self):
    #     """
    #     Flush, set the target to None and lose the buffer.
    #     """
    #     self.flush()
