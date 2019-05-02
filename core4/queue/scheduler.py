#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
This module implements :class:`.CoreScheduler`.

To start a scheduler from Python goes like this::

    from core4.queue.scheduler import CoreScheduler

    scheduler = CoreScheduler()
    scheduler.start

To stop the worker start a new Python interpreter and go with::

    from core4.queue.main import CoreQueue

    queue = CoreQueue()
    queue.halt(now=True)

.. note:: use :ref:`coco` to achieve the same with::

    $ coco --scheduler
    $ coco --halt
"""

import datetime

from croniter import croniter

import core4.const
import core4.service.introspect.main
import core4.util.node
from core4.queue.daemon import CoreDaemon
from core4.service.introspect.command import ENQUEUE


class CoreScheduler(CoreDaemon):
    """
    The scheduler enqueues jobs available in core4 projects installed on the
    same node. The scheduler queries the ``schedule`` property of all known
    :class:`.CoreJob` implementations.

    The timing information in the ``schedule`` attribute uses cron format (see
    https://en.wikipedia.org/wiki/Cron). core4 uses :mod:`croniter` to parse
    and to calculate schedules.

    Note that the scheduler keeps track of the last scheduling time and catches
    up with all missed enqueuing, e.g. if the scheduler was down.
    """
    kind = "scheduler"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.schedule = None
        self.next = None
        self.previous = None
        self.job = None

    def startup(self):
        """
        Implements the **startup** phase of the scheduler. The method is based
        on :class:`.CoreDaemon` implementation and additionally spawns
        :meth:`.collect_job`.
        """
        super().startup()
        self.collect_job()

    def loop(self):
        """
        This is the main processing phase of the scheduler.
        """
        self.wait_time = 1
        self.previous = None
        doc = self.config.sys.job.find_one({"_id": "__schedule__"})
        if doc:
            self.previous = doc.get("schedule_at", None)
        super().loop()

    def run_step(self):
        """
        The scheduler consists of one step. This time interval of this step
        can be configured by core4 config setting ``scheduler.interval`` and
        defaults to 1 second.
        :return:
        """
        jobs = self.get_next(self.previous, self.at)
        n = 0
        for job, schedule in jobs:
            self.logger.info("enqueue [%s] at [%s]", job, schedule)
            # todo: improve no try/except required if functool.enqueue used
            try:
                self.queue.enqueue(name=job)._id
            except ImportError:
                core4.service.introspect.main.exec_project(
                    job, ENQUEUE, qual_name=job)
            except core4.error.CoreJobExists:
                self.logger.error("job [%s] exists", job)
            except Exception:
                self.logger.critical("failed to enqueue [%s]", job,
                                     exc_info=True)
            else:
                n += 1
        self.previous = self.at
        self.config.sys.job.update_one(
            {
                "_id": "__schedule__"
            },
            update={
                "$set": {
                    "schedule_at": self.previous
                }
            },
            upsert=True
        )
        return n

    def get_next(self, start, end):
        """
        Returns the jobs to be enqueued between ``start`` and ``end``
        date/time.

        :param start: :class:`datetime.datetime` when last scheduling has been
                      executed. Pass ``None`` for the very first schedule.
        :param end: :class:`datetime.datetime` of now
        :return: list of tuples with ``(name, schedule)`` of the job
        """
        ret = []
        if start is None:
            start = end
        for job_name, doc in self.job.items():
            cron = croniter(doc["schedule"], start)
            next_time = cron.get_next(datetime.datetime)
            if next_time <= end:
                ret.append((job_name, doc["schedule"]))
        return ret
