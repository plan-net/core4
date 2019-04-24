import os

import pytest
from core4.api.v1.application import CoreApiContainer
from core4.api.v1.request.role.main import RoleHandler
from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.request.standard.access import AccessHandler
from tests.api.test_response import setup, LocalTestServer, StopHandler
from core4.base.main import CoreBase
import pymongo
import pymongo.errors

_ = setup

# curr_dir = os.path.abspath(os.curdir)
#
# ASSET_FOLDER = '../asset'
# MONGO_URL = 'mongodb://core:654321@localhost:27017'
# MONGO_DATABASE = 'core4test'

class HandlerTest(CoreRequestHandler):
    author = "mra"

    def get(self):
        out = "{}\n{}".format(self.config.sys.queue.connection,
                              self.config.sys.queue.async)
        self.reply(out)

class CoreApiTestServer(CoreApiContainer):
    rules = [
        (r'/kill', StopHandler),
        (r'/test', HandlerTest),
    ]


class HttpServer(LocalTestServer):

    def start(self, *args, **kwargs):
        return CoreApiTestServer


@pytest.fixture()
def http():
    server = HttpServer()
    yield server
    server.stop()


def test_base():
    base = CoreBase()
    assert isinstance(base.config.sys.queue.connection, pymongo.MongoClient)
    assert not base.config.sys.queue.async

def test_handler(http):
    rv = http.get("/test")
    out = rv.json()["data"].split("\n")
    assert out[0].startswith("MotorClient")
    assert out[1].strip() == "True"
