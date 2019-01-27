"""
This module implements the core4 job process spawned by :class:`.CoreWorker`.
"""

import ctypes
import io
import os
import sys
import tempfile
import traceback

import datetime
from bson.objectid import ObjectId

import core4.base.main
import core4.error
import core4.logger.mixin
import core4.queue.job
import core4.queue.main
import core4.util.node

libc = ctypes.CDLL(None)
c_stdout = ctypes.c_void_p.in_dll(libc, 'stdout')
c_stderr = ctypes.c_void_p.in_dll(libc, 'stderr')


class CoreWorkerProcess(core4.base.main.CoreBase,
                        core4.logger.mixin.CoreLoggerMixin):
    """
    This class controls jobs execution. It loads the requested job from
    ``sys.queue``, drops user privileges,
    :meth:`.execute <core4.queue.job.CoreJob.execute>` the job, manages the
    final job state (``complete`` or ``failed``) and set the jobs' cookie
    ``last_runtime``. Finally job output to ``STDOUT`` is saved into
    ``sys.stdout``.
    """

    def start(self, job_id, redirect=True):
        """
        :param job_id: str representing a :class:`bson.objectid.ObjectId`
        """
        _id = ObjectId(job_id)
        self.identifier = _id
        self.setup_logging()
        self.queue = core4.queue.main.CoreQueue()
        now = core4.util.node.mongo_now()
        job = self.load_job(_id)

        update = {
            "locked.pid": core4.util.node.get_pid()
        }
        if job.inactive_at is None:
            update["inactive_at"] = now + datetime.timedelta(
                seconds=job.defer_max)
            self.logger.debug("set inactive_at [%s]", update["inactive_at"])
        ret = self.config.sys.queue.update_one(
            filter={"_id": job._id}, update={"$set": update})
        if ret.raw_result["n"] != 1:
            raise RuntimeError(
                "failed to update job [{}] state [starting]".format(job._id))
        for k, v in update.items():
            job.__dict__[k] = v
        if job.inactive_at <= now:
            self.queue.set_inactivate(job)
            return

        job.logger.info("start execution")
        self.drop_privilege()

        if redirect:
            self.original_stdout_fd = sys.stdout.fileno()
            saved_stdout_fd = os.dup(self.original_stdout_fd)
            tfile = tempfile.TemporaryFile(mode='w+b')
            self._redirect_stdout(tfile.fileno())

        self.queue.make_stat("start_job", str(job_id))
        job.add_exception_logger()
        # job.args.pop("manual_execute", None)
        try:
            job.execute(**job.args)
        except core4.error.CoreJobDeferred:
            self.queue.set_defer(job)
            return False
        except:
            job.__dict__["attempts_left"] -= 1
            # job.logger.critical("failed", exc_info=True)
            self.queue.set_failed(job)
            return False
        else:
            job.__dict__["attempts_left"] -= 1
            self.queue.set_complete(job)
            job.cookie.set("last_runtime", job.finished_at)
            job.progress(1.0, "execution end marker", force=True)
            return True
        finally:
            if redirect:
                # todo: this one is a race condition in testing
                self._redirect_stdout(saved_stdout_fd)
                tfile.flush()
                tfile.seek(0, io.SEEK_SET)
                body = tfile.read()
                try:
                    u8body = body.decode('utf-8')
                except:
                    u8body = body
                self.config.sys.stdout.update_one(
                    filter={
                        "_id": job._id,
                    },
                    update={
                        "$set": {
                            "timestamp": core4.util.node.mongo_now(),
                            "stdout": u8body
                        }
                    },
                    upsert=True
                )
                os.close(saved_stdout_fd)
                tfile.close()

    def _redirect_stdout(self, to_fd):
        """
        Redirect stdout to the given file descriptor.
        """
        libc.fflush(c_stdout)
        sys.stdout.close()
        os.dup2(to_fd, self.original_stdout_fd)
        sys.stdout = io.TextIOWrapper(os.fdopen(self.original_stdout_fd, 'wb'))

    def drop_privilege(self):
        # todo: requires impelmentation
        pass

    def load_job(self, _id):
        try:
            return self.queue.load_job(_id)
        except:
            exc_info = sys.exc_info()
            update = {
                "state": core4.queue.job.STATE_ERROR,
                "last_error": {
                    "exception": repr(exc_info[1]),
                    "timestamp": core4.util.node.mongo_now(),
                    "traceback": traceback.format_exception(*exc_info)
                }
            }
            ret = self.config.sys.queue.update_one(
                filter={"_id": _id}, update={"$set": update})
            if ret.raw_result["n"] != 1:
                raise RuntimeError(
                    "failed to update job [{}] state [starting]".format(_id))
            self.logger.info("failed to start [%s]", _id)
            self.queue.make_stat("failed_start", str(_id))
            return None
