import logging
import os

import pytest

from pprint import pprint
import core4.logger.mixin
from core4.queue.job import CoreJob
from core4.service.introspect import CoreIntrospector
from tests.util import asset
from core4.service.setup import CoreSetup


@pytest.fixture(autouse=True)
def reset(tmpdir):
    logging.shutdown()
    # logging mixin (setup complete)
    core4.logger.mixin.CoreLoggerMixin.completed = False
    # setup
    os.environ["CORE4_CONFIG"] = asset("config/empty.yaml")
    core4.logger.mixin.logon()
    yield
    # singletons
    core4.util.Singleton._instances = {}
    # os environment
    dels = []
    for k in os.environ:
        if k.startswith('CORE4_'):
            dels.append(k)
    for k in dels:
        del os.environ[k]


class HiddenJob(CoreJob):
    hidden = True
    author = "mra"
    schedule = "1 2 3 4 5"


class NoAuthorJob(HiddenJob):
    pass


class OkJob(HiddenJob):
    """
    this job is ok
    """
    author = 'mra'


def test_load():
    intro = CoreIntrospector()
    jobs = list(intro.iter_job())
    assert [j for j in jobs if j["name"] == "core4.queue.job.DummyJob"]
    assert not [j for j in jobs if j["name"] == "core4.queue.job.CoreJob"]
    hidden_job = [j for j in jobs if "HiddenJob" in j["name"]][0]
    assert hidden_job["hidden"]
    no_author_job = [j for j in jobs if "NoAuthorJob" in j["name"]][0]
    assert not no_author_job["valid"]
    assert "missing author" in no_author_job["exception"]["exception"]
    ok_job = [j for j in jobs if "OkJob" in j["name"]][0]
    assert ok_job["schedule"] is None
    assert "this job is ok" in ok_job["doc"]
    #pprint(jobs)

def test_discover():
    setup = CoreSetup()
    jobs = setup.collect_jobs()
    for pro in ("tests", "project", "core4"):
        assert pro in jobs.keys()
        assert "version" in jobs[pro].keys()
        assert "name" in jobs[pro].keys()
        assert "title" in jobs[pro].keys()
        assert "built" in jobs[pro].keys()
    assert "core4.queue.job.DummyJob" in jobs["core4"]["job"]