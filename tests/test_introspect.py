import pytest
import logging
import core4.logger.mixin
from tests.util import asset
import os
from core4.service.introspect import CoreIntrospector

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

def test_load():
    intro = CoreIntrospector()
    intro._load()
