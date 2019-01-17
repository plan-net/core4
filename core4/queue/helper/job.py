import datetime as dt
import requests
import tornado.template

import core4.util
from core4.queue.job import CoreJob
import core4.const


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


if __name__ == '__main__':
    from core4.queue.helper.functool import execute
    execute(DummyJob)
