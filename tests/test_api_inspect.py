import pytest

import core4.logger.mixin
from core4.service.introspect.api import CoreApiInspector

pytest.fixture()


def setup():
    core4.logger.mixin.logon()


def test_init():
    inspect = CoreApiInspector()
    inspect.info("core4.api.v1.server.CoreApiServer")
    inspect.info("core4.api.v1.server.CoreApiServerXXX")
    inspect.info("core4.api.v1.server.XXX.CoreApiServer")
    inspect.info("project.api.server1.ProjectServer1")
