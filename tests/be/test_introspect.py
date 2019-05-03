import logging
import os
import pytest
from pprint import pprint
import core4.logger.mixin
from core4.queue.job import CoreJob
from core4.service.introspect.main import CoreIntrospector
from tests.be.util import asset
from core4.queue.scheduler import CoreScheduler

MONGO_URL = 'mongodb://core:654321@localhost:27017'
MONGO_DATABASE = 'core4test'

@pytest.fixture(autouse=True)
def reset(tmpdir):
    logging.shutdown()
    # logging mixin (setup complete)
    core4.logger.mixin.CoreLoggerMixin.completed = False
    # setup
    os.environ["CORE4_CONFIG"] = asset("config/empty.yaml")
    os.environ["CORE4_OPTION_logging__stderr"] = "DEBUG"
    os.environ["CORE4_OPTION_DEFAULT__mongo_url"] = MONGO_URL
    os.environ["CORE4_OPTION_DEFAULT__mongo_database"] = MONGO_DATABASE
    os.environ["CORE4_OPTION_logging__mongodb"] = "DEBUG"

    os.environ["CORE4_OPTION_folder__home"] = "/home/mra/core4home"

    core4.logger.mixin.logon()
    yield
    # singletons
    core4.util.tool.Singleton._instances = {}
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

def test_create():
    intro = CoreIntrospector()
    intro.run(capture=False)
    for project in intro.project:
        print(project)
        pprint(project.module)
        print("jobs")
        pprint(list(project.jobs))
        print("api containner")
        pprint(list(project.api_containers))
        print("modules")
        pprint(project._modules)
        print()

def test_introspect():
    intro = CoreIntrospector()
    for project in intro.introspect():
        pprint(project)

def test_jobs():
    intro = CoreIntrospector()
    j = []
    for project in intro.introspect():
        for job in project["jobs"]:
            print(job["name"], job["schedule"], job["valid"])
            j.append(job["name"])
    print(sorted(j))

def test_schedule():
    scheduler = CoreScheduler()
    scheduler.collect_job()


def test_container():
    intro = CoreIntrospector()
    for project in intro.introspect():
        print(project["name"])
        for container in project["api_containers"]:
            print(container["name"])
