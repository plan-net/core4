"""
This module implements the core4 job process spawned by :class:`.CoreWorker`.
"""

import ctypes
import io
import os
import sys
import tempfile

from bson.objectid import ObjectId

import core4.base
import core4.error
import core4.logger.mixin
import core4.queue.job
import core4.queue.main
import core4.util

libc = ctypes.CDLL(None)
c_stdout = ctypes.c_void_p.in_dll(libc, 'stdout')
c_stderr = ctypes.c_void_p.in_dll(libc, 'stderr')


class CoreWorkerProcess(core4.base.CoreBase,
                        core4.logger.mixin.CoreLoggerMixin):
    """
    This class controls jobs execution. It loads the requested job from
    ``sys.queue``, drops user privileges,
    :meth:`.execute <core4.queue.job.CoreJob.execute>` the job, manages the
    final job state (``complete`` or ``failed``) and set the jobs' cookie
    ``last_runtime``. Finally job output to ``STDOUT`` is saved into
    ``sys.stdout``.
    """

    def start(self, job_id):
        """
        :param job_id: str representing a :class:`bson.objectid.ObjectId`
        """
        _id = ObjectId(job_id)
        self.identifier = _id
        self.setup_logging()
        self.queue = core4.queue.main.CoreQueue()
        job = self.queue.load_job(_id)
        self.drop_privilege()

        self.original_stdout_fd = sys.stdout.fileno()
        saved_stdout_fd = os.dup(self.original_stdout_fd)
        tfile = tempfile.TemporaryFile(mode='w+b')
        self._redirect_stdout(tfile.fileno())

        try:
            job.execute(**job.args)
        except core4.error.CoreJobDeferred:
            self.queue.set_defer(job)
        except:
            job.__dict__["attempts_left"] -= 1
            self.queue.set_failed(job)
        else:
            job.__dict__["attempts_left"] -= 1
            self.queue.set_complete(job)
            job.cookie.set("last_runtime", job.finished_at)
            job.progress(1.0, "execution end marker", force=True)
        finally:
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
                        "timestamp": core4.util.mongo_now(),
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


def _start():
    # internal method used by CoreWorker object to spawn a new
    #   Python interpreter executing the job
    proc = CoreWorkerProcess()
    proc.start(str(sys.stdin.read()).strip())
