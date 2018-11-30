import os

import pytest

from core4.api.v1.application import CoreApiContainer
from core4.api.v1.request.main import CoreRequestHandler
from tests.api.test_response import setup, LocalTestServer, StopHandler

print(setup)


class RenderingHandler(CoreRequestHandler):

    def get(self, variant):
        if variant == "1":
            self.render("template/test1.html")
        elif variant == "2":
            self.render("template/not_found.html")
        elif variant == "3":
            file_path = os.path.dirname(__file__)
            file_name = os.path.join(file_path, "template/test1.html")
            self.render(file_name)


class DirectoryHandler(CoreRequestHandler):
    template_path = "template1"

    def get(self, variant):
        if variant == "1":
            self.render("test2.html")
        elif variant == "2":
            self.render("test1.html")
        elif variant == "3":
            self.render_default("simple.css")


class CoreApiTestServer(CoreApiContainer):
    enabled = True
    rules = [
        (r'/kill', StopHandler),
        (r'/render/(.+)', RenderingHandler),
        (r'/directory/(.+)', DirectoryHandler)
    ]


class HttpServer(LocalTestServer):

    def start(self, *args, **kwargs):
        return CoreApiTestServer


@pytest.fixture()
def http():
    server = HttpServer()
    yield server
    server.stop()


def test_server_test(http):
    rv = http.get("/profile")
    assert rv.status_code == 200


def test_render(http):
    rv = http.get("/render/1")
    assert rv.status_code == 200
    assert "hello world" in str(rv.content)

    rv = http.get("/render/2")
    assert rv.status_code == 500

    rv = http.get("/render/3")
    assert "hello world" in str(rv.content)


def test_static_folder(http):
    rv = http.get("/directory/1")
    assert rv.status_code == 200
    assert "this is template 2" in str(rv.content)


def test_static_not_found(http):
    rv = http.get("/directory/2")
    assert rv.status_code == 500
    assert "FileNotFoundError" in str(rv.content)


def test_default(http):
    rv = http.get("/directory/3")
    assert rv.status_code == 200
    assert rv.content.decode("utf-8").startswith("body")

def test_url_func(http):
    rv = http.get("/render/1")
    assert rv.status_code == 200
    assert "hello world" in str(rv.content)
    print(rv.content)



if __name__ == '__main__':
    from core4.api.v1.tool import serve, serve_all
    serve_all(filter=["project.api", "core4.api.v1.server",
                      "example"])  # , name=sys.argv[1], port=int(sys.argv[2]))
    # from core4.api.v1.server import CoreApiServer
    # serve(CoreApiTestServer, CoreApiServer)
