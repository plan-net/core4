import datetime as dt
import tornado.template

import core4.logger
import core4.queue.main
import core4.queue.worker
import core4.service.setup
import core4.util
import core4.util.node
from core4.queue.job import CoreJob


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
    doc = enqueue(job, **kwargs)
    worker = core4.queue.worker.CoreWorker(name="manual")
    if not worker.start_job(doc, spawn=False):
        queue = core4.queue.main.CoreQueue()
        queue.remove_job(doc._id)
        worker.remove_jobs()


class DummyJob(CoreJob):
    """
    This is just a job-dummy for testing purposes.
    """
    author = 'mra'

    def execute(self, *args, **kwargs):
        import time
        sleep = kwargs.get("sleep", None) or 3
        until = core4.util.node.now() + dt.timedelta(seconds=sleep)
        self.logger.info("just sleeping [%s] seconds", sleep)
        n = 0
        while core4.util.node.now() <= until:
            n += 1
            print("line %d at %s" % (n, core4.util.node.now()))
            p = float(
                sleep - (until
                         - core4.util.node.now()).total_seconds()) / sleep
            self.progress(p, "running")
            time.sleep(0.5)


class MailerJob(CoreJob):
    """
    This job takes the template location (absolute path), recipients, subject
    line and any additional arguments and sends an email.
    """
    author = 'mra'

    def execute(self, template, recipients, subject, *args, **kwargs):
        msg = []
        if not isinstance(recipients, list):
            recipients = [recipients]
        msg.append("FROM: ?")
        msg.append("TO: %s" % (", ".join(recipients)))
        msg.append("SUBJECT: %s" % (subject))
        msg.append("")
        t = tornado.template.Template(template)
        kwargs["recipients"] = ", ".join(recipients)
        kwargs["subject"] = subject
        for k, v in kwargs.items():
            msg.append("variable %s = %s" % (k, v))
        msg.append(t.generate(**kwargs).decode("utf-8"))
        print("\n".join(msg))
        self.logger.debug("send mail:\n%s", "\n".join(msg))