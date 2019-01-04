import core4.logger
import core4.queue.main
import core4.service.setup
import core4.queue.worker
import core4.util


def enqueue(job, **kwargs):
    """
    Helper method to enqueue a job.

    :param job: qual_name or job class
    """
    if isinstance(job, str):
        kwargs["name"] = job
    else:
        kwargs["cls"] = job
    queue = core4.queue.main.CoreQueue()
    return queue.enqueue(**kwargs)


def execute(job, **kwargs):
    """
    Helper method to enqueue and immediatly execute a job in foreground. This
    method is used in development::

        execute(DummyJob, sleep=15)


    :param job: qual_name or job class
    :param kwargs: job arguments
    """
    setup = core4.service.setup.CoreSetup()
    setup.make_all()
    core4.logger.logon()
    kwargs["manual_execute"] = core4.util.node.mongo_now().isoformat()
    enq_doc = enqueue(job, **kwargs)
    worker = core4.queue.worker.CoreWorker(name="manual")
    worker.at = core4.util.node.mongo_now()
    worker.start_job(enq_doc.serialise(), async=False)
    while True:
        doc = worker.queue.job_detail(enq_doc._id)
        if doc is not None:
            if doc.get("journaled", False):
                break
    #worker.queue.remove_job(enq_doc._id)
    #worker.remove_jobs()