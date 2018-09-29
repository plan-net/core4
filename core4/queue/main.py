from core4.base import CoreBase
from core4.queue.job import STATE_PENDING
import core4.error
import importlib
import core4.service.setup
import pymongo.errors


class CoreQueue(CoreBase):

    def enqueue(self, cls=None, name=None, **kwargs):
        """
        Enqueues the passed job identified by it's :meth:`.qual_name`. The job
        is represented by a document in MongoDB collection ``sys.queue``.

        :param **kwargs: dict
        :return: enqueued job object
        """
        core4.service.setup.CoreSetup().make_queue()
        job = self.job_factory(name or cls, **kwargs)
        doc = job.serialise()
        job.__dict__["state"] = STATE_PENDING
        try:
            ret = self.config.sys.queue.insert_one(doc)
        except pymongo.errors.DuplicateKeyError as exc:
            raise core4.error.CoreJobExists(
                "job [{}] exists with args {}".format(
                    job.qual_name(), job.args))
        job.__dict__["_id"] = ret.inserted_id
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

