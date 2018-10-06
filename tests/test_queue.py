# -*- coding: utf-8 -*-


import core4.error
import core4.queue.job
import core4.queue.main
from tests.pytest_util import *


def test_job_found():
    q = core4.queue.main.CoreQueue()
    q.enqueue(core4.queue.job.DummyJob)


def test_job_not_found():
    q = core4.queue.main.CoreQueue()
    with pytest.raises(core4.error.CoreJobNotFound):
        q.enqueue("DummyJob")


def test_no_class():
    q = core4.queue.main.CoreQueue()
    with pytest.raises(TypeError):
        q.enqueue(pytest)


def test_no_module():
    q = core4.queue.main.CoreQueue()
    with pytest.raises(ImportError):
        q.enqueue("notfound.job")


def test_no_module2():
    q = core4.queue.main.CoreQueue()
    with pytest.raises(ImportError):
        q.enqueue("123notfound.job")
    with pytest.raises(ImportError):
        q.enqueue("123 notfound.job")


def test_no_mro():
    q = core4.queue.main.CoreQueue()

    class T:
        def __init__(self, *args, **kwargs):
            pass

    with pytest.raises(TypeError):
        q.enqueue(T())


def test_no_mro2():
    q = core4.queue.main.CoreQueue()

    class Test: pass

    with pytest.raises(TypeError):
        q.enqueue(Test())


def test_no_mro3():
    q = core4.queue.main.CoreQueue()

    class Test: pass

    with pytest.raises(TypeError):
        q.enqueue(Test)


def test_enqueue():
    q = core4.queue.main.CoreQueue()
    q.enqueue(core4.queue.job.DummyJob)


def test_enqueue_args():
    q = core4.queue.main.CoreQueue()
    q.enqueue(core4.queue.job.DummyJob, a1=1, a2=2, a3=3)
    with pytest.raises(core4.error.CoreJobExists):
        q.enqueue(core4.queue.job.DummyJob, args={"a1": 1, "a2": 2, "a3": 3})
    q.enqueue(core4.queue.job.DummyJob)
    with pytest.raises(core4.error.CoreJobExists):
        q.enqueue(core4.queue.job.DummyJob)


def test_invalid():
    q = core4.queue.main.CoreQueue()

    class T1(core4.queue.job.CoreJob): pass

    with pytest.raises(AssertionError):
        q.enqueue(T1)

    class T2(core4.queue.job.CoreJob):
        author = 'mra'

    q.enqueue(T2)

def test_project_maintenance():
    q = core4.queue.main.CoreQueue()
    assert not q.maintenance('project')
    q.enter_maintenance('project')
    q.enter_maintenance('project1')
    q.leave_maintenance('XXX')
    assert q.maintenance('project')
    assert q.maintenance('project1')
    q.leave_maintenance('project')
    assert q.maintenance('project1')
    assert not q.maintenance('project')
    q.leave_maintenance('project1')
    assert not q.maintenance('project1')
