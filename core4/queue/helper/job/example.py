import datetime as dt
import time
import core4.util.node
from core4.queue.job import CoreJob
from core4.util.core_email import MailMixin


class DummyJob(CoreJob):
    """
    This is just a job-dummy for testing purposes.
    """
    author = 'mra'
    # schedule = '* * * * *'

    def execute(self, *args, **kwargs):
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


class EmailJob(MailMixin, CoreJob):
    """
    This job sends an email by receiving all needed parameters as job-arguments.
    """
    author = "mkr"

    def execute(self, *args, **kwargs):
        self.send_mail(*args, **kwargs)
