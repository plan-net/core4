import importlib
import sys
import pymongo.errors
from datetime import timedelta
import core4.error
import core4.service.setup
import core4.util
from core4.base import CoreBase
from core4.queue.job import STATE_PENDING
import traceback

STATE_WAITING = (core4.queue.job.STATE_DEFERRED,
                 core4.queue.job.STATE_FAILED)
STATE_STOPPED = (core4.queue.job.STATE_KILLED,
                 core4.queue.job.STATE_INACTIVE,
                 core4.queue.job.STATE_ERROR)

class CoreQueue(CoreBase): #, metaclass=core4.util.Singleton):

    def enqueue(self, cls=None, name=None, by=None, **kwargs):
        """
        Enqueues the passed job identified by it's :meth:`.qual_name`. The job
        is represented by a document in MongoDB collection ``sys.queue``.

        :param **kwargs: dict
        :return: enqueued job object
        """
        core4.service.setup.CoreSetup().make_queue()
        job = self.job_factory(name or cls, **kwargs)
        # update job properties
        job.__dict__["attempts_left"] = job.__dict__["attempts"]
        job.__dict__["state"] = STATE_PENDING
        enqueued_from = {
            "at": lambda: core4.util.mongo_now(),
            "hostname": lambda: core4.util.get_hostname(),
            "parent_id": lambda: None,
            "username": lambda: core4.util.get_username()
        }
        if by is None:
            by = {}
        job.__dict__["enqueued"] = {}
        for k in ("at", "hostname", "parent_id", "username"):
            job.__dict__["enqueued"][k] = by.get(k, enqueued_from[k]())
        # save
        doc = job.serialise()
        try:
            ret = self.config.sys.queue.insert_one(doc)
        except pymongo.errors.DuplicateKeyError as exc:
            raise core4.error.CoreJobExists(
                "job [{}] exists with args {}".format(
                    job.qual_name(), job.args))
        job.__dict__["_id"] = ret.inserted_id
        job.__dict__["identifier"] = ret.inserted_id
        self.logger.info(
            'successfully enqueued [%s] with [%s]', job.qual_name(), job._id)
        return job

    def job_factory(self, job, **kwargs):
        """
        Takes the fully qualified job name, identifies and imports the job class
        and returns the job class.

        :param job_name: fully qualified name of the job
        :return: job class
        """
        try:
            if isinstance(job, str):
                parts = job.split(".")
                package = ".".join(parts[:-1])
                if not package:
                    raise core4.error.CoreJobNotFound(
                        "[{}] not found".format(job))
                class_name = parts[-1]
                module = importlib.import_module(package)
                cls = getattr(module, class_name)
            else:
                cls = job
            if not isinstance(cls, type):
                raise TypeError(
                    "{} not a class".format(repr(job)))
            obj = cls(**kwargs)
            if not isinstance(obj, core4.queue.job.CoreJob):
                raise TypeError(
                    "{} not a subclass of CoreJob".format(repr(job)))
            obj.validate()
            return obj
        except:
            self.logger.exception(
                "cannot instantiate job {} ".format(repr(job)))
            raise

    def enter_maintenance(self):
        ret = self.config.sys.worker.update_one(
            {"_id": "__maintenance__"},
            update={
                "$set": {
                    "timestamp": core4.util.now()
                }
            },
            upsert=True
        )
        return ret.raw_result["n"] == 1

    def leave_maintenance(self):
        ret = self.config.sys.worker.delete_one({"_id": "__maintenance__"})
        return ret.raw_result["n"] == 1

    def maintenance(self):
        return self.config.sys.worker.count({"_id": "__maintenance__"}) > 0

    def halt(self, past=None, now=None):
        if now is not None:
            ret = self.config.sys.worker.update_one(
                {"_id": "__halt__"},
                update={"$set": {"timestamp": core4.util.now()}},
                upsert=True)
            return ret.raw_result["n"] == 1
        elif past is not None:
            return self.config.sys.worker.count(
                {"_id": "__halt__", "timestamp": {"$gte": past}}) > 0
        else:
            raise core4.error.Core4UsageError(".halt requires now or past")

    def remove_job(self, _id):
        at = core4.util.now()
        ret = self.config.sys.queue.update_one(
            {
                "_id": _id,
                "removed_at": None
            },
            update={
                "$set": {
                    "removed_at": at
                }
            }
        )
        if ret.raw_result["n"] == 1:
            self.logger.warning(
                "flagged job [%s] to be remove at [%s]", _id, at)
            return True
        self.logger.error("failed to flag job [%s] to be remove", _id)
        return False

    def restart_job(self, _id):
        if self._restart_waiting(_id):
            self.logger.warning('successfully restarted [%s]', _id)
            return _id
        else:
            new_id = self._restart_stopped(_id)
            if new_id:
                self.logger.warning('successfully restarted [%s] '
                                    'with [%s]', _id, new_id)
                return new_id
            else:
                self.logger.error("failed to restart [%s]", _id)
                return _id

    def _restart_waiting(self, _id):
        ret = self.config.sys.queue.update_one(
            {
                "_id": _id,
                "state": {
                    "$in": STATE_WAITING
                }
            },
            update={
                "$set": {
                    "query_at": None
                }
            }
        )
        return ret.raw_result["n"] == 1

    def _restart_stopped(self, _id):
        job = self.find_job(_id)
        if job.state in STATE_STOPPED:
            if self.lock_job('__user__', _id):
                ret = self.config.sys.queue.delete_one({"_id": _id})
                if ret.raw_result["n"] == 1:
                    enqueue = job.enqueued
                    enqueue["parent_id"] = job._id
                    enqueue["at"] = core4.util.mongo_now()
                    doc = dict([(k, v) for k, v in job.serialise().items() if k in core4.queue.job.ENQUEUE_ARGS])
                    new_job = self.enqueue(name=job.qual_name(), by=enqueue, **doc)
                    job.enqueued["child_id"] = new_job._id
                    self.journal(job.serialise())
                    return new_job._id
        return None

    def kill_job(self, _id):
        at = core4.util.now()
        ret = self.config.sys.queue.update_one(
            {
                "_id": _id,
                "killed_at": None,
                "state": core4.queue.job.STATE_RUNNING
            },
            update={
                "$set": {
                    "killed_at": at
                }
            }
        )
        if ret.raw_result["n"] == 1:
            self.logger.warning(
                "flagged job [%s] to be killed at [%s]", _id, at)
            return True
        self.logger.error("failed to flag job [%s] to be killed", _id)
        return False

    def lock_job(self, identifier, _id):
        try:
            self.config.sys.lock.insert_one(
                {"_id": _id, "worker": identifier})
            self.logger.debug('successfully reserved [%s]', _id)
            return True
        except pymongo.errors.DuplicateKeyError:
            self.logger.debug('failed to reserve [%s]', _id)
        return False

    def unlock_job(self, _id):
        ret = self.config.sys.lock.delete_one({"_id": _id})
        if ret.raw_result["n"] == 1:
            self.logger.debug('successfully released [%s]', _id)
            return True
        self.logger.error('failed to release [%s]', _id)
        return False

    def journal(self, doc):
        ret = self.config.sys.journal.insert_one(doc)
        return ret.inserted_id == doc["_id"]

    def _find_job(self, _id, collection):
        doc = collection.find_one({"_id": _id})
        if doc is None:
            raise core4.error.CoreJobNotFound(
                "failed to load job [{}]".format(_id))
        job = self.job_factory(doc["name"]).deserialise(**doc)
        return job

    def load_job(self, _id):
        return self._find_job(_id, self.config.sys.queue)

    def find_job(self, _id):
        try:
            return self.load_job(_id)
        except core4.error.CoreJobNotFound:
            return self._find_job(_id, self.config.sys.journal)
        except:
            raise

    def set_complete(self, job):
        self.logger.debug(
            "updating job [%s] to [%s]", job._id,
            core4.queue.job.STATE_COMPLETE)
        runtime = self.finish(job, core4.queue.job.STATE_COMPLETE)
        self.update_job(job, "state", "finished_at", "runtime", "locked",
                        "trial")
        self.logger.debug("journaling job [%s]", job._id)
        job = self.load_job(job._id)
        ret = self.config.sys.journal.insert_one(job.serialise())
        if ret.inserted_id is None:
            raise RuntimeError(
                "failed to journal job [{}]".format(job._id))
        self.logger.debug("removing completed job [%s]", job._id)
        ret = self.config.sys.queue.delete_one(filter={"_id": job._id})
        if ret.deleted_count != 1:
            raise RuntimeError(
                "failed to remove job [{}] from queue".format(job._id))
        job.logger.info("done execution with [complete] "
                        "after [%d] sec.", runtime)

    def set_killed(self, job):
        self.logger.debug(
            "updating job [%s] to [%s]", job._id,
            core4.queue.job.STATE_KILLED)
        runtime = self.finish(job, core4.queue.job.STATE_KILLED)
        job.__dict__["last_error"] = {
            "exception": "JobKilledByWorker",
            "timestamp": core4.util.mongo_now(),
            "traceback": None
        }
        self.update_job(job, "state", "runtime", "locked",
                        "trial", "last_error")
        job.logger.critical("done execution with [%s] after [%d] sec.",
                            job.state, runtime)

    def finish(self, job, state):
        job.__dict__["state"] = state
        job.__dict__["finished_at"] = core4.util.mongo_now()
        runtime = (job.finished_at - job.started_at).total_seconds()
        job.__dict__["runtime"] = (job.runtime or 0.) + runtime
        job.__dict__["locked"] = None
        return runtime

    def add_exception(self, job):
        exc_info = sys.exc_info()
        job.__dict__["last_error"] = {
            "exception": repr(exc_info[1]),
            "timestamp": core4.util.mongo_now(),
            "traceback": traceback.format_exception(*exc_info)
        }

    def inactivate_job(self, job):
        self.logger.debug("inactivate job [%s]", job._id)
        runtime = self.finish(job, core4.queue.job.STATE_INACTIVE)
        self.update_job(job, "state", "finished_at", "runtime", "locked",
                        "trial")
        job.logger.critical("done execution with [inactive] "
                            "after [%d] sec. and [%d] trials in [%s]", runtime,
                            job.trial, job.inactive_at - job.enqueued["at"])

    def set_failed(self, job):
        if job.attempts_left > 0:
            state = core4.queue.job.STATE_FAILED
            job.__dict__["query_at"] = (core4.util.mongo_now()
                                        + timedelta(seconds=job.error_time))
        else:
            state = core4.queue.job.STATE_ERROR
        self.logger.debug("updating job [%s] to [%s]", job._id, state)
        runtime = self.finish(job, state)
        self.add_exception(job)
        self.update_job(job, "state", "finished_at", "runtime", "locked",
                        "last_error", "attempts_left", "query_at", "trial")
        job.logger.error("done execution with [%s] "
                         "after [%d] sec. and [%d] attempts to go: %s\n%s",
                         state, runtime, job.attempts_left,
                         job.last_error["exception"],
                         "\n".join(job.last_error["traceback"]))

    def update_job(self, job, *args):
        ret = self.config.sys.queue.update_one(
            filter={"_id": job._id},
            update={"$set": dict([(k, getattr(job, k)) for k in args])})
        if ret.raw_result["n"] != 1:
            raise RuntimeError(
                "failed to update job [{}] state [%s]".format(
                    job._id, job.state))

    def set_defer(self, job):
        state = core4.queue.job.STATE_DEFERRED
        now = core4.util.mongo_now()
        job.__dict__["query_at"] = now + timedelta(seconds=job.defer_time)
        self.logger.debug("updating job [%s] to [%s]", job._id, state)
        runtime = self.finish(job, state)
        self.add_exception(job)
        self.update_job(job, "state", "finished_at", "runtime", "locked",
                        "last_error", "query_at", "trial")
        job.logger.info("done execution with [deferred] "
                        "after [%d] sec. and [%s] to go: %s", runtime,
                        job.inactive_at - now, job.last_error["exception"])

