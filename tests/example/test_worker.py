from bson.objectid import ObjectId

import core4.queue.helper.functool
from core4.queue.helper.job.example import DummyJob


# This example uses manual setup/teardown and executes a job with a worker
# thread


def test_worker(tearup, worker):
    _id = core4.queue.helper.functool.enqueue(DummyJob, sleep=5)
    while True:
        ret = worker.find_job(_id=ObjectId(_id))
        if not ret:
            break
        print([j["state"] for j in ret])

