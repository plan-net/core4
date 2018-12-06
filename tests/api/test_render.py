import multiprocessing
from pprint import pprint

import pytest
import requests
import time
import tornado.gen
from tornado.ioloop import IOLoop

import core4.error
from core4.api.v1.application import CoreApiContainer
from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.tool import serve
from tests.api.test_response import setup

_ = setup


class InternalHandler1(CoreRequestHandler):
    title = "internal test 1"

    def get(self):
        assert self.application.container.root is None
        assert self.application.container.get_root() == "/tests"
        list1 = list(self.application.container.iter_rule())
        list2 = list(self.application.container.iter_rule())
        assert list1 == list2

    def post(self):
        self.reply(self.title)


class InternalHandler2(InternalHandler1):
    title = "internal test 2"

    def get(self):
        assert self.application.container.root == "test1"
        assert self.application.container.get_root() == "/test1"


class RenderingHandler(CoreRequestHandler):
    title = "rendering handler"

    def get(self):
        self.render("template/test.html")


class RenderingHandler1(RenderingHandler):
    title = "rendering handler 1"

    def get(self):
        self.render("template/test.html")


class RenderingHandler2(RenderingHandler):
    title = "rendering handler 2"

    def get(self):
        self.render("template/test1.html")


class RenderingHandler3(RenderingHandler):
    title = "rendering handler 3"
    template_path = "template"

    def get(self):
        self.render_default("card.html", GET=None)

class CardHandler(RenderingHandler):
    title = "card handler"
    card_link = "http://www.serviceplan.com"

    def get(self):
        return self.reply("hello from CardHandler")


class StopHandler(CoreRequestHandler):
    protected = False

    def get(self):
        self.logger.warning("stop IOLoop now: %s", IOLoop.current())
        IOLoop.current().stop()


class CoreApiTestServer1(CoreApiContainer):
    enabled = True
    rules = [
        (r'/kill', StopHandler),
        (r'/internal', InternalHandler1),
        (r'/card', CardHandler),
        # (r'/render/(.+)', RenderingHandler),
        # (r'/directory/(.+)', DirectoryHandler)
    ]


class CoreApiTestServer2(CoreApiContainer):
    enabled = True
    root = "test1"
    rules = [
        (r'/internal', InternalHandler2),
        (r'/internal1', InternalHandler1, {"title": "custom title 1"}),
        (r'/render', RenderingHandler),
        (r'/render1', RenderingHandler1),
        (r'/render2', RenderingHandler2),
        (r'/render3', RenderingHandler3)
    ]


class CoreApiTestErrorServer1(CoreApiContainer):
    enabled = True
    rules = [
        (r'/internal', InternalHandler1),
        (r'/internal', InternalHandler2)
    ]


class CoreApiTestErrorServer2(CoreApiContainer):
    enabled = True
    rules = [
        (r'/internal', InternalHandler1)
    ]


class CoreApiTestErrorServer3(CoreApiContainer):
    enabled = True
    rules = [
        (r'/internal', int)
    ]


class HttpServer:

    def __init__(self, *args):
        self.cls = args
        self.port = 5555
        self.process = None
        self.process = multiprocessing.Process(target=self.run)
        self.process.start()
        while True:
            try:
                url = self.url("/core4/api/v1/profile")
                requests.get(url, timeout=1)
                break
            except:
                pass
            time.sleep(1)
            tornado.gen.sleep(1)
        self.signin = requests.get(
            self.url("/core4/api/v1/login?username=admin&password=hans"))
        self.token = self.signin.json()["data"]["token"]
        assert self.signin.status_code == 200

    def url(self, url):
        return "http://localhost:{}".format(self.port) + url

    def request(self, method, url, **kwargs):
        if self.token:
            kwargs.setdefault("headers", {})[
                "Authorization"] = "Bearer " + self.token
        return requests.request(method, self.url(url), **kwargs)

    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self.request("POST", url, **kwargs)

    def put(self, url, **kwargs):
        return self.request("PUT", url, **kwargs)

    def delete(self, url, **kwargs):
        return self.request("DELETE", url, **kwargs)

    def run(self):
        serve(*self.cls, port=self.port)

    def stop(self):
        rv = self.get("/tests/kill")
        assert rv.status_code == 200
        self.process.join()


@pytest.fixture()
def http():
    server = HttpServer(CoreApiTestServer1, CoreApiTestServer2)
    yield server
    server.stop()


def test_server_test(http):
    rv = http.get("/core4/api/v1/profile")
    assert rv.status_code == 200
    rv = http.get("/tests/internal")
    assert rv.status_code == 200
    rv = http.get("/test1/internal")
    assert rv.status_code == 200
    rv = http.get("/core4/api/v1/info")
    assert rv.status_code == 200
    # pprint(rv.json())
    lh = 'core4.api.v1.request.standard.login.LoginHandler'
    login_handler = [h for h in rv.json()["data"]
                     if h["qual_name"] == lh][0]
    rv = http.get(login_handler["route"][0]["help_url"])
    assert rv.status_code == 200
    ret = rv.json()["data"]
    assert ret["author"] == "mra"
    assert ret["qual_name"] == "core4.api.v1.request.standard.login." \
                               "LoginHandler"


def test_title_args(http):
    rv = http.post("/tests/internal")
    assert rv.status_code == 200
    assert "internal test 1" == rv.json()["data"]
    rv = http.post("/test1/internal1")
    assert rv.status_code == 200
    assert "custom title 1" == rv.json()["data"]
    rv = http.get("/core4/api/v1/info")
    assert rv.status_code == 200
    qn = 'tests.api.test_render.InternalHandler1'
    internal_handler = [h for h in rv.json()["data"] if h["qual_name"] == qn]
    internal_handler[0]["route"][0]["title"] == "custom title 1"
    internal_handler[0]["route"][1]["title"] == "internal test 1"
    # pprint(internal_handler)


def test_help(http):
    rv = http.post("/tests/internal")
    assert rv.status_code == 200
    rv = http.get("/core4/api/v1/info")
    assert rv.status_code == 200
    qn = 'tests.api.test_render.InternalHandler1'
    internal_handler = [h for h in rv.json()["data"] if h["qual_name"] == qn]
    url = internal_handler[0]["route"][0]["help_url"]
    rv = http.get(url)
    assert rv.status_code == 200
    pprint(rv.json())
    data = rv.json()["data"]
    assert data["route"]["title"] == "custom title 1"
    assert "get" in data["doc"]
    assert "post" in data["doc"]


def test_server_not_unique():
    with pytest.raises(core4.error.Core4SetupError):
        serve(CoreApiTestErrorServer1)
    with pytest.raises(core4.error.Core4SetupError):
        serve(CoreApiTestServer1, CoreApiTestErrorServer2)


def test_server_wrong_args():
    with pytest.raises(core4.error.Core4SetupError):
        serve(CoreApiTestErrorServer3)


def test_card(http):
    rv = http.get("/core4/api/v1/info")
    assert rv.status_code == 200
    qn = 'tests.api.test_render.InternalHandler1'
    internal_handler = [h for h in rv.json()["data"] if h["qual_name"] == qn]
    internal_handler[0]["route"][0]["title"] == "custom title 1"
    internal_handler[0]["route"][1]["title"] == "internal test 1"

    c1 = internal_handler[0]["route"][0]["card_url"]
    c2 = internal_handler[0]["route"][1]["card_url"]
    rv = http.get(c1)
    assert rv.status_code == 200
    content = rv.content.decode('utf-8')
    assert "custom title 1" in content
    assert "tests.api.test_render.InternalHandler1" in content
    assert 'href="/test1/internal1"' in content

    rv = http.get(c2)
    assert rv.status_code == 200
    content = rv.content.decode('utf-8')
    assert "internal test 1" in content
    assert "tests.api.test_render.InternalHandler1" in content
    assert 'href="/tests/internal"' in content


def test_render(http):
    rv = http.get("/test1/render")
    assert rv.status_code == 200
    body = rv.content.decode("utf-8")
    url = "/core4/api/v1/file/project" \
          "/db53cbff74c1ad855fe519eeda2ee677" \
          "/2f9c7924e975f580eaa242d56654182e" \
          "/template/test.css"
    assert url in body
    rv = http.get(url)
    assert 'body {\n    font-family: monospace;\n' \
           '    color: red;\n' \
           '    font-size: 3em;\n' \
           '}' in rv.content.decode("utf-8")
    url = "/core4/api/v1/file/project" \
          "/db53cbff74c1ad855fe519eeda2ee677" \
          "/2f9c7924e975f580eaa242d56654182e/template/head.png"
    rv = http.get(url)
    assert rv.content[0:10] == b'\x89PNG\r\n\x1a\n\x00\x00'
    assert rv.content[-10:] == b'\x00\x00IEND\xaeB`\x82'

    url = "/core4/api/v1/file/default" \
          "/db53cbff74c1ad855fe519eeda2ee677" \
          "/2f9c7924e975f580eaa242d56654182e/favicon.ico"
    rv = http.get(url)
    assert rv.content[0:10] == b'\x00\x00\x01\x00\x03\x00\x10\x10\x00\x00'
    assert rv.content[-10:] == b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'


def test_render_title(http):
    rv = http.get("/test1/render")
    assert rv.status_code == 200
    body = rv.content.decode("utf-8")
    "hello world: rendering handler" in body

    rv = http.get("/test1/render1")
    assert rv.status_code == 200
    body = rv.content.decode("utf-8")
    "hello world: rendering handler 1" in body
    css = '/core4/api/v1/file' \
          '/project' \
          '/3fafc251fdbbd7fe76b21b2b3e2ae532' \
          '/6633bad7e2f6813257693276a5cfa6d8' \
          '/template/test.css'
    assert 'href="' + css + '"' in body
    rv = http.get(css)
    assert rv.status_code == 200
    css_body = rv.content.decode("utf-8")
    assert "// test css" in css_body


def test_render_default(http):
    rv = http.get("/test1/render2")
    assert rv.status_code == 200
    body = rv.content.decode("utf-8")
    "hello world: rendering handler 2" in body
    css = '/core4/api/v1/file' \
          '/default' \
          '/9b5aa0c1a256cb9551ccde906d912d03' \
          '/d55c5bcb1c6b46d31e007c20248f68f9' \
          '/default.css'
    assert 'href="' + css + '"' in body
    css_nf1 = "/core4/api/v1/file" \
              "/project" \
              "/9b5aa0c1a256cb9551ccde906d912d03" \
              "/d55c5bcb1c6b46d31e007c20248f68f9" \
              "/not_found.css"
    assert 'href="' + css_nf1 + '"' in body
    css_nf2 = "/core4/api/v1/file" \
              "/default" \
              "/9b5aa0c1a256cb9551ccde906d912d03" \
              "/d55c5bcb1c6b46d31e007c20248f68f9" \
              "/not_found.css"
    assert 'href="' + css_nf2 + '"' in body

    rv = http.get(css)
    assert rv.status_code == 200
    css_body = rv.content.decode("utf-8")
    assert "// core4 default css" in css_body

    rv = http.get(css_nf1)
    assert rv.status_code == 404

    rv = http.get(css_nf2)
    assert rv.status_code == 404


def test_render_template(http):
    rv = http.get("/test1/render3")
    assert rv.status_code == 200


def test_card_handler(http):
    rv = http.get("/tests/card")
    assert rv.status_code == 200
    print(rv.content)
    card = "0f465136b6238198edf0ce3576e52b96/f30b6d2fb2e3ab8a3f90ccd483f17ac1"
    rv = http.get("/core4/api/v1/info/card/" + card)
    assert rv.status_code == 200
    print(rv.content)


if __name__ == '__main__':
    # from core4.api.v1.tool import serve, serve_all
    # serve_all(filter=[
    #     "project.api",
    #     "core4.api.v1.server",
    #     "example"])
    serve(CoreApiTestServer1, CoreApiTestServer2)
