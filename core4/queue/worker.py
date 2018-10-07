"""
This module implements the core4 worker. Together with :mod:`core4.queue.main`
and :mod:`core4.queue.process` it delivers a simple producer/consumer pattern
for job execution.
"""

import os
import subprocess
import sys
import traceback

import psutil
import pymongo
import pymongo.errors
import time
from datetime import timedelta

import core4.base
import core4.error
import core4.queue.job
import core4.queue.main
import core4.service.setup
import core4.util

#: processing steps in the main loop of :class:`.CoreWorker`
STEPS = (
    "work_jobs",
    "remove_jobs",
    "flag_jobs",
    "collect_stats")


class CoreWorker(core4.base.CoreBase):
    """
    This class is the working horse to carry and execute jobs. Workers have an
    identifier. This identifier defaults to the hostname of the worker and must
    be unique across the cluster.

    Each worker operates in three distinct phases. Each phase features one or
    more processing steps.

    #. **startup** - registers the worker abd available projects, do some
       housekeeping/ cleanup, and several prerequisites, e.g. required
       folders and MongoDB collections are verified
    #. **loop** - work and manage jobs, collect server statistics
    #. **shutdown** - again some housekeeping and unregistering the worker
       and projects
    #. **exit** - quit worker

    .. warning:: The worker ``.identifier`` must be unique.
    """

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.identifier = kwargs.get("name", None) or core4.util.get_hostname()
        self.hostname = core4.util.get_hostname()
        self.phase = {
            "startup": core4.util.now(),
            "loop": None,
            "shutdown": None,
            "exit": None
        }
        self.plan = None
        self.exit = False
        self.at = None
        self.cycle = dict([(s, 0) for s in STEPS])
        self.cycle["total"] = 0
        self.offset = None
        self.queue = core4.queue.main.CoreQueue()

    def start(self):
        """
        executes the worker's workflow from :meth:`.startup` to the main
        processing :meth:`.loop` to :meth:`.shutdown`.
        :return:
        """
        self.startup()
        self.loop()
        self.shutdown()
        self.enter_phase("exit")

    def startup(self):
        """
        Implements the **startup** phase of the worker.
        """
        self.register_worker()
        self.enter_phase("startup")
        self.create_worker_env()
        self.register_projects()
        self.cleanup()
        self.plan = self.create_plan()

    def register_worker(self):
        """
        Registers the worker identified by it's ``.identifier`` in collection
        ``sys.worker``.

        .. warning:: please note that the ``.identifier`` of the worker must
                     not exist.
        """
        self.config.sys.worker.update_one(
            {"_id": self.identifier},
            update={
                "$set": {
                    "phase": {},
                    "heartbeat": None,
                    "plugins": None
                }
            },
            upsert=True
        )
        self.logger.info("registered worker")

    def register_projects(self):
        # todo: implement
        pass

    def shutdown(self):
        """
        Shutdown the worker by spawning the final housekeeping
        method :meth:`cleanup`.
        """
        self.enter_phase("shutdown")
        self.cleanup()

    def create_worker_env(self):
        """
        Ensures proper environment setup with required folders and roles.
        This method utilises :class:`core4.service.setup.CoreSetup`.
        """
        setup = core4.service.setup.CoreSetup()
        setup.make_folder()
        setup.make_role()  # todo: implement!
        setup.make_stdout()
        self.create_stats()

    def create_stats(self):
        pass

    def cleanup(self):
        """
        General housekeeping method of the worker.
        :return:
        """
        ret = self.config.sys.lock.delete_many({"worker": self.identifier})
        self.logger.info(
            "cleanup removed [%d] sys.lock records", ret.raw_result["n"])

    def create_plan(self):
        """
        Creates the worker's execution plan in the main processing loop:

        # :meth:`.work_jobs` - get next job, inactivate or execute
        # :meth:`.remove_jobs` - remove jobs
        # :meth:`.flag_jobs` - flag jobs as non-stoppers, zombies, killed
        # :meth:`.collect_stats` - collect and save general sever metrics

        :return: dict with step ``name``, ``interval``, ``next`` timestamp
                 to execute and method reference ``call``
        """
        plan = []
        now = core4.util.now()
        self.wait_time = None
        for s in STEPS:
            interval = self.config.worker.execution_plan[s]
            if self.wait_time is None:
                self.wait_time = interval
            else:
                self.wait_time = min(interval, self.wait_time)
            self.logger.debug("set [%s] interval [%1.2f] sec.", s, interval)
            plan.append({
                "name": s,
                "interval": interval,
                "next": now + timedelta(seconds=interval),
                "call": getattr(self, s)
            })
        self.logger.debug(
            "create execution plan with cycle time [%1.2f] sec.",
            self.wait_time)
        return plan

    def enter_phase(self, phase):
        """
        This method advertises current execution phase in collection
        ``sys.worker``.

        :param phase: current phase
        """
        self.phase[phase] = core4.util.mongo_now()
        ret = self.config.sys.worker.update_one(
            {"_id": self.identifier},
            update={
                "$set": {
                    "phase.{}".format(phase): self.phase[phase]
                }
            }
        )
        if ret.raw_result["n"] == 1:
            self.logger.info("enter phase [%s]", phase)
        else:
            raise core4.error.Core4SetupError(
                "failed to enter phase [{}]".format(phase))

    def loop(self):
        """
        This is the main processing phase of the worker entered by
        :meth:`.start`. This method skips processing if core4 system is in the
        general *maintenance* state indicated in collection ``sys.worker``.

        The loop is left if core4 system is in the general *__halt__* state as
        indicated in collection ``sys.worker``, too.
        """
        time.sleep(self.wait_time)  # start with cycle 1
        self.enter_phase("loop")
        in_maintenance = False
        while not self.exit:
            self.cycle["total"] += 1
            if self.queue.halt(at=self.phase["startup"]):
                return
            if self.queue.maintenance():
                if not in_maintenance:
                    in_maintenance = True
                    self.logger.info("entering maintenance")
            else:
                if in_maintenance:
                    in_maintenance = False
                    self.logger.info("leaving maintenance")
                self.at = core4.util.now()
                for step in self.plan:
                    interval = timedelta(seconds=step["interval"])
                    if step["next"] <= self.at:
                        self.logger.debug("enter [%s] at cycle [%s]",
                                          step["name"], self.cycle["total"])
                        step["call"]()
                        self.logger.debug("exit [%s] at cycle [%s]",
                                          step["name"], self.cycle["total"])
                        step["next"] = self.at + interval
            time.sleep(self.wait_time)

    def work_jobs(self):
        """
        This method is part of the main :meth:`.loop` phase of the worker

        The step queries and handles the best next job from ``sys.queue`` (see
        :meth:`.get_next_job` and :meth:`.start_job`). Furthermore this method
        *inactivates* jobs.
        """
        doc = self.get_next_job()
        if doc is None:
            return
        try:
            job = self.queue.job_factory(doc["name"]).deserialise(**doc)
        except:
            # very early exception, so fail hard
            exc_info = sys.exc_info()
            update = {
                "state": core4.queue.job.STATE_ERROR,
                "started_at": self.at,
                "last_error": {
                    "exception": repr(exc_info[1]),
                    "traceback": traceback.format_exception(*exc_info),
                }
            }
            self.logger.error(
                "unexpected error during job instantiation", exc_info=exc_info)
            ret = self.config.sys.queue.update_one(
                filter={"_id": doc["_id"]},
                update={"$set": update})
            if ret.raw_result["n"] != 1:
                raise RuntimeError(
                    "failed to update job [{}] state [{}]".format(
                        doc["_id"], core4.queue.job.STATE_FAILED))
        else:
            if job.inactive_at and job.inactive_at <= self.at:
                self.queue.set_inactivate(job)
            else:
                self.start_job(job)

    def get_next_job(self):
        """
        Queries the best next job from collection ``sys.queue``. This method
        filters and orders jobs with the following properties:

        **filter:**

        * not ``locked``
        * with ``attempts_left``
        * in waiting state (``pending``, ``failed`` or ``deferred``)
        * eligable for this or all worker (``.identifier``)
        * not removed, yet (``.removed_at``)
        * not killed, yet (``.killed_at``)
        * with no or past query time (``.query_at``)

        **sort order:**

        * ``.force``
        * ``.priority``
        * enqueue date/time (job ``.id`` sort order)

        The method memorises an ``offset`` attribute to ensure all jobs have a
        chance to get queries across multiple workers. If all jobs have been
        checked, then the offset is reset and querying starts from top.

        In order to handle high priority jobs, the existence of a job *below*
        the current offset is checked. If a job with a higher priority exists
        below the ``offset``, then this high-priority job is returned.

        :return: job document from collection ``sys.queue``
        """
        query = [
            {'locked': None},
            {'attempts_left': {'$gt': 0}},
            {'$or': [
                {'state': s} for s in [
                    core4.queue.job.STATE_PENDING,
                    core4.queue.job.STATE_FAILED,
                    core4.queue.job.STATE_DEFERRED]]
            },
            {'$or': [{'worker': self.identifier},
                     {'worker': None}]},
            {'removed_at': None},
            {'killed_at': None},
            {'$or': [{'query_at': {'$lte': self.at}},
                     {'query_at': None}]},
        ]
        order = [
            ('force', pymongo.DESCENDING),
            ('priority', pymongo.DESCENDING),
            ('_id', pymongo.ASCENDING)
        ]
        if self.offset:
            cur2 = self.config.sys.queue.find(
                filter={'$and': query + [{"_id": {"$lte": self.offset}}]},
                sort=order)
            query.append({'_id': {'$gt': self.offset}})
        else:
            cur2 = None
        cur1 = self.config.sys.queue.find(
            filter={'$and': query}, sort=order)
        while True:
            try:
                data = cur1.next()
            except StopIteration:
                data = None
            if cur2 is not None:
                try:
                    data2 = cur2.next()
                except StopIteration:
                    data2 = None
            else:
                data2 = None
            if data is None:
                if data2 is None:
                    self.offset = None
                    return None
                self.logger.debug(
                    "next job from top chunk [%s]", data2["_id"])
                data = data2
            else:
                self.logger.debug(
                    "next job from bottom chunk [%s]", data["_id"])
                if data2 is not None and data2["priority"] > data["priority"]:
                    data = data2
                    self.logger.debug(
                        "next job from prioritised top chunk [%s]",
                        data["_id"])
            project = data["name"].split(".")[0]
            if self.queue.maintenance(project):
                self.logger.debug(
                    "skipped job [%s] in maintenance", data["_id"])
                continue
            if not self.queue.lock_job(self.identifier, data["_id"]):
                self.logger.debug('skipped job [%s] due to lock failure',
                                  data["_id"])
                continue
            self.offset = data["_id"]
            self.logger.debug('successfully reserved [%s]', data["_id"])
            return data

    def start_job(self, job):
        """
        Spawns the passed job by launching a seperate Python interpreter and
        communicating the job ``_id``.

        This method updates the job ``state``, ``started_at`` timestamp,
        increases the ``trial``, sets the ``locked`` property, calculates the
        ``inactive_at`` timestamp if not done, yet and resets the ``query_at``
        attribute.

        The execution process is spawned using :mod:`subprocess`
        :class:`.Popen` and replicates current OS environment. Method
        :func:`start` form :mod:`core4.queue.process` consumes the execution
        request.

        .. note:: This method does not call :meth:`.unlock_job`. This is done
                  by :func:`start` of :mod:`core4.queue.process`

        :param job: :class:`.CoreJob` object
        """
        at = core4.util.mongo_now()
        update = {
            "state": core4.queue.job.STATE_RUNNING,
            "started_at": at,
            "query_at": None,
            "trial": job.trial + 1,
            "locked": {
                "at": self.at,
                "heartbeat": self.at,
                "hostname": self.hostname,
                "pid": None,
                "progress_value": None,
                "progress": None,
                "worker": self.identifier,
                "username": None  # todo: this one is not set, yet
            }
        }
        if job.inactive_at is None:
            update["inactive_at"] = at + timedelta(
                seconds=job.defer_max)
            self.logger.debug("set inactive_at [%s]", update["inactive_at"])
        ret = self.config.sys.queue.update_one(
            filter={"_id": job._id}, update={"$set": update})
        if ret.raw_result["n"] != 1:
            raise RuntimeError(
                "failed to update job [{}] state [starting]".format(job._id))
        for k, v in update.items():
            job.__dict__[k] = v
        try:
            executable = job.find_executable()
        except:
            self.fail_hard(job)
        else:
            job.logger.info("start execution with [%s]", executable)
            try:
                proc = subprocess.Popen(
                    [
                        executable,
                        "-c", "from core4.queue.process import _start; "
                              "_start()"
                    ],
                    env=os.environ,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE
                )
            except:
                self.fail_hard(job)
            else:
                ret = self.config.sys.queue.update_one(
                    filter={
                        "_id": job._id
                    },
                    update={
                        "$set": {
                            "locked.pid": proc.pid
                        }
                    }
                )
                if ret.raw_result["n"] != 1:
                    raise RuntimeError(
                        "failed to update job [{}] pid [{}]".format(
                            job._id, proc.pid))
                job_id = str(job._id).encode("utf-8")
                proc.stdin.write(bytes(job_id))
                proc.stdin.close()
                self.logger.debug("successfully launched job [%s] with [%s]",
                                  job._id, executable)

    def fail_hard(self, job):
        """
        This method puts the job into ``error`` state due to early exceptions
        before the job has even been launched. These issues arise either at
        job class instantiation or subprocessing with
        :mod:`core4.queue.process`.

        :param job: :class:`core4.queue.job.CoreJob` object
        """
        self.logger.error("failed to instantiate job", exc_info=True)
        job.__dict__["attempts_left"] = 0
        self.queue.set_failed(job)

    def remove_jobs(self):
        """
        This method is part of the main :meth:`.loop` phase of the worker.

        The processing step queries all jobs with a specified ``removed_at``
        attribute. After successful job lock, the job is moved from
        ``sys.queue`` into ``sys.journal``.

        .. note:: This method does not unlock the job from ``sys.lock``. This
                  special behavior is required to prevent race conditions
                  between multiple workers simultaneously removing *and*
                  locking the job between ``sys.queue`` and ``sys.lock``.
        """

        cur = self.config.sys.queue.find(
            {"removed_at": {"$ne": None}}
        )
        for doc in cur:
            if self.queue.lock_job(self.identifier, doc["_id"]):
                if self.queue.journal(doc):
                    ret = self.config.sys.queue.delete_one({"_id": doc["_id"]})
                    if ret.raw_result["n"] != 1:
                        raise RuntimeError(
                            "failed to remove job [{}]".format(doc["_id"]))
                    self.logger.info(
                        "successfully journaled and removed job [%s]",
                        doc["_id"])
                    # note: we will not unlock the job to prevent race
                    # conditions with other workds; this will be settled
                    # with .cleanup
                    continue
                self.logger.error(
                    "failed to journal and remove job [%s]", doc["_id"])

    def flag_jobs(self):
        """
        This method is part of the main :meth:`.loop` phase of the worker.

        The method queries all jobs in state ``running`` locked by the current
        worker and forward processing to

        # identify and flag non-stopping jobs (see :meth:`.flag_nonstop`),
        # identify and flag zombies (see :meth:`.flag_zombie`),
        # identify and handle died jobs (see :meth:`.check_pid`), and to
        # manage jobs requested to be kill (see :meth:`.kill_pid`)
        """
        cur = self.config.sys.queue.find(
            {
                "state": core4.queue.job.STATE_RUNNING,
                "locked.worker": self.identifier
            },
            projection=[
                "_id", "wall_time", "wall_at", "zombie_time", "zombie_at",
                "started_at", "locked.heartbeat", "locked.pid", "killed_at"
            ]
        )
        for doc in cur:
            self.flag_nonstop(doc)
            self.flag_zombie(doc)
            self.check_pid(doc)
            self.kill_pid(doc)

    def flag_nonstop(self, doc):
        """
        Identifies non-stopping jobs which exceeded their runtime beyond the
        specified ``wall_at`` timestamp.

        .. note:: The ``wall_time`` attribute represents the timestamp when
                  the job was flagged. Job execution continues without further
                  action.

        :param doc: job MongoDB document
        """
        if doc["wall_time"] and not doc["wall_at"]:
            if doc["started_at"] < (self.at
                                    - timedelta(seconds=doc["wall_time"])):
                ret = self.config.sys.queue.update_one(
                    filter={
                        "_id": doc["_id"]
                    },
                    update={"$set": {"wall_at": core4.util.mongo_now()}})
                if ret.raw_result["n"] == 1:
                    self.logger.warning(
                        "successfully set non-stop job [%s]", doc["_id"])

    def flag_zombie(self, doc):
        """
        Identifies zombie jobs which have not updated their ``heartbeat`` (in
        ``.locked`` attribute) for date/time range specified in the
        ``.zombie_time`` attribute.

        The jobs' :meth:`.progress <core4.queue.job.CoreJob.progress>` method
        updates the ``heartbeat``. Therefore job developers are expected to
        call this method for long-running algorithms regularly.

        .. note:: The ``zombie_at`` attribute represents the timestamp when
                  the job was flagged. Job execution continues without further
                  action.

        :param doc: job MongoDB document
        """
        if not doc["zombie_at"]:
            if doc["locked"]["heartbeat"] < (self.at
                                             - timedelta(
                        seconds=doc["zombie_time"])):
                ret = self.config.sys.queue.update_one(
                    filter={
                        "_id": doc["_id"]
                    },
                    update={"$set": {"zombie_at": core4.util.mongo_now()}})
                if ret.raw_result["n"] == 1:
                    self.logger.warning(
                        "successfully set zombie job [%s]", doc["_id"])

    def check_pid(self, doc):
        (found, proc) = self.pid_exists(doc)
        if not found and proc:
            self.logger.error("pid [%s] not exists, killing",
                              doc["locked"]["pid"])
            job = self.queue.load_job(doc["_id"])
            self.queue.set_killed(job, "JobKilled")

    def kill_pid(self, doc):
        """
        Handles jobs which have been requested to be killed. If the process
        exists, then it is killed and the job state is set to ``killed``.

        :param doc: job MongoDB document
        """
        if doc["killed_at"]:
            (found, proc) = self.pid_exists(doc)
            if found and proc:
                proc.kill()
                job = self.queue.load_job(doc["_id"])
                self.queue.set_killed(job)

    def pid_exists(self, doc):
        """
        Returns ``True`` if the job exists and its OS state is _DEAD_ or
        _ZOMBIE_. The :class:`psutil.Process` object is also returned for
        further action.

        :param doc: job MongoDB document
        :return: tuple of ``True`` or ``False`` and the job process or None
        """
        proc = None
        if doc["locked"] and doc["locked"]["pid"]:
            if psutil.pid_exists(doc["locked"]["pid"]):
                proc = psutil.Process(doc["locked"]["pid"])
                if proc.status() not in (psutil.STATUS_DEAD,
                                         psutil.STATUS_ZOMBIE):
                    return (True, proc)
        return (False, proc)

    def collect_stats(self):
        # todo: should update worker's heartbeat, too
        pass


if __name__ == '__main__':
    from core4.logger.mixin import logon

    logon()
    CoreWorker().start()
