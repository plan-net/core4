"""
This module implements the core4 job process spawned by :class:`.CoreWorker`.
"""

import sys

from bson.objectid import ObjectId

import core4.base
import core4.error
import core4.logger.mixin
import core4.queue.job
import core4.queue.main
import core4.util


class CoreWorkerProcess(core4.base.CoreBase,
                        core4.logger.mixin.CoreLoggerMixin):
    """
    This class controls jobs execution. It loads the requested job from
    ``sys.queue``, drops user privileges,
    :meth:`.execute <core4.queue.job.CoreJob.execute>` the job, manages the
    final job state (``complete`` or ``failed``) and set the jobs' cookie
    ``last_runtime``.
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
        try:
            job.execute(**job.args)
            job.__dict__["attempts_left"] -= 1
            self.queue.set_complete(job)
            job.cookie.set("last_runtime", job.finished_at)
            job.progress(1.0, "execution end marker", force=True)
        except core4.error.CoreJobDeferred:
            self.queue.set_defer(job)
        except:
            job.__dict__["attempts_left"] -= 1
            self.queue.set_failed(job)

    def drop_privilege(self):
        # todo: requires impelmentation
        pass


def _start():
    # internal method used by CoreWorker object to spawn a new
    #   Python interpreter executing the job
    proc = CoreWorkerProcess()
    proc.start(str(sys.stdin.read()).strip())
