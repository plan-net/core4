
from core4.queue.helper.functool import execute
from core4.queue.job import CoreJob
from core4.queue.helper.job import ApiJob

class TestJob(CoreJob):

    author = "mra"

    def execute(self, **kwargs):
        print("OK")


if __name__ == '__main__':
    execute(ApiJob)