import core4.logger
import core4.queue.helper
import core4.queue.job
import core4.queue.main


class ErrorJob(core4.queue.job.CoreJob):
    """
    This is a simple example job
    """

    author = 'mra'
    error_time = 3
    attempts = 3

    def execute(self, *args, **kwargs):
        if kwargs.get("success", False):
            if self.attempts_left == 1:
                return
        time.sleep(kwargs.get("sleep", 0))
        raise RuntimeError("expected failure")


class DeferJob(core4.queue.job.CoreJob):
    author = 'mra'
    defer_time = 2
    defer_max = 10

    def execute(self, *args, **kwargs):
        if not kwargs.get("success", False) or self.trial < 3:
            self.defer("expected defer with trial [%d]", self.trial)
        time.sleep(10)


if __name__ == '__main__':
    core4.logger.logon()
    q = core4.queue.main.CoreQueue()
    # q.enqueue(ErrorJob)
    q.enqueue(core4.queue.helper.DummyJob)
