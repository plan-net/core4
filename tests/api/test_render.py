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
from core4.api.v1.tool.functool import serve
from tests.api.test_response import setup

_ = setup


class InternalHandler1(CoreRequestHandler):
    title = "internal test 1"

    def get(self):
        assert self.application.container.root is None
        assert self.application.container.get_root() == "/tests"
        list1 = list(self.application.container.iter_rule())
        list2 = list(self.application.container.iter_rule())
        assert str(list1) == str(list2)

    def post(self):
        self.reply(self.title)


class InternalHandler2(InternalHandler1):
    title = "internal test 2"

    def get(self):
        assert self.application.container.root == "test1"
        assert self.application.container.get_root() == "/test1"


class RenderingHandler1(CoreRequestHandler):
    title = "rendering handler 1"

    def get(self, num=None):
        if num == "relative":
            # relative to handler path
            return self.render("web/test1.html")
        if num == "absolute":
            # absolute to project path
            return self.render("/api/web/test1.html")
        self.render("web/test_xxx.html")


class RenderingHandler2(RenderingHandler1):
    title = "rendering handler 2"
    template_path = "web"

    def get(self, num=None):
        if num == "relative":
            # relative to handler path
            return self.render("test1.html")
        if num == "absolute":
            # absolute to project path
            return self.render("/api/web/test1.html")
        self.render("web/test_xxx.html")


class RenderingHandler3(RenderingHandler1):
    title = "rendering handler 3"
    template_path = "web"
    static_path = "web"

    def get(self, num=None):
        self.render("test2.html")


# todo: requires testing
# class CardHandler(RenderingHandler1):
#     title = "card handler"
#     enter_url = "http://www.serviceplan.com"
#
#     def get(self):
#         return self.reply("hello from CardHandler")


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
    ]


class CoreApiTestServer2(CoreApiContainer):
    enabled = True
    root = "test1"
    rules = [
        (r'/internal', InternalHandler2),
        (r'/internal1', InternalHandler1, {"title": "custom title 1"}),
        (r'/render2.1/?(.*)', RenderingHandler2,
         {"static_path": "web2", "title": "custom title render2.1"}),
        (r'/render2.2/?(.*)', RenderingHandler2, {"template_path": "/api/web2",
                                                  "title": "custom title render2.2"}),
        (r'/render2/?(.*)', RenderingHandler2),
        (r'/render3', RenderingHandler3),
        (r'/render/?(.*)', RenderingHandler1),
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
    base_url = ""
    def __init__(self, *args):
        self.cls = args
        self.port = 5555
        self.process = None
        self.process = multiprocessing.Process(target=self.run)
        self.process.start()
        while True:
            try:
                url = self.url("/core4/api/profile")
                requests.get(url, timeout=1)
                break
            except:
                pass
            time.sleep(1)
            tornado.gen.sleep(1)
        self.signin = requests.get(
            self.url("/core4/api/login?username=admin&password=hans"))
        self.token = self.signin.json()["data"]["token"]
        assert self.signin.status_code == 200

    def url(self, url, base=True, absolute=False):
        if base:
            b = self.base_url
        else:
            b = ""
        if absolute:
            return url
        hostname = core4.util.node.get_hostname()
        return "http://{}:{}{}".format(hostname, self.port, b) + url

    def request(self, method, url, base, absolute, **kwargs):
        if self.token:
            kwargs.setdefault("headers", {})[
                "Authorization"] = "Bearer " + self.token
        return requests.request(method, self.url(url, base, absolute),
                                **kwargs)

    def get(self, url, base=True, absolute=False, **kwargs):
        return self.request("GET", url, base, absolute, **kwargs)

    def post(self, url, base=True, absolute=False, **kwargs):
        return self.request("POST", url, base, absolute, **kwargs)

    def put(self, url, base=True, absolute=False, **kwargs):
        return self.request("PUT", url, base, absolute, **kwargs)

    def delete(self, url, base=True, absolute=False, **kwargs):
        return self.request("DELETE", url, base, absolute, **kwargs)

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
    rv = http.get("/core4/api/profile")
    assert rv.status_code == 200
    rv = http.get("/tests/internal")
    assert rv.status_code == 200
    rv = http.get("/test1/internal")
    assert rv.status_code == 200
    rv = http.get("/core4/api/info?per_page=100")
    assert rv.status_code == 200
    pprint(rv.json())
    lh = 'core4.api.v1.request.standard.login.LoginHandler'
    login_handler = [h for h in rv.json()["data"]
                     if h["qual_name"] == lh][0]
    print(login_handler)
    rv = http.get(login_handler["endpoint"][0]["help_url"], absolute=True)
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
    rv = http.get("/core4/api/info?per_page=100")
    assert rv.status_code == 200
    pprint(rv.json())
    qn = 'tests.api.test_render.InternalHandler1'
    internal_handler = [h for h in rv.json()["data"]
                        if h["qual_name"] == qn]
    assert len(internal_handler) == 2
    # print(internal_handler)
    # internal_handler[0]["title"] == "custom title 1"
    # internal_handler[1]["title"] == "internal test 1"
    # pprint(internal_handler)


def test_help(http):
    rv = http.post("/tests/internal")
    assert rv.status_code == 200
    rv = http.get("/core4/api/info?per_page=100")
    assert rv.status_code == 200
    qn = 'tests.api.test_render.InternalHandler1'
    pprint(rv.json())
    internal_handler = [h for h in rv.json()["data"]
                        if h["qual_name"] == qn]

    # for ih in internal_handler:
    #     print("+++")
    #     url = ih["help_url"]
    #     rv = http.get(url, absolute=True)
    #     assert rv.status_code == 200
    #     pprint(rv.json())

    ih = [h for h in rv.json()["data"]
          if h["route_id"] == "2a3897ef4e61542912a0cf3f3ab5a32f"][0]
    url = ih["endpoint"][0]["help_url"]
    rv = http.get(url, absolute=True)
    assert rv.status_code == 200
    pprint(rv.json())
    data = rv.json()["data"]
    assert data["title"] == "custom title 1"
    assert len([m for m in data["method"] if m["method"] == "get"]) == 1
    assert len([m for m in data["method"] if m["method"] == "post"]) == 1
    assert len([m for m in data["method"] if m["method"] == "put"]) == 0
    assert len([m for m in data["method"] if m["method"] == "delete"]) == 0


def test_server_not_unique():
    with pytest.raises(core4.error.Core4SetupError):
        serve(CoreApiTestErrorServer1)
    with pytest.raises(core4.error.Core4SetupError):
        serve(CoreApiTestServer1, CoreApiTestErrorServer2)


def test_server_wrong_args():
    with pytest.raises(core4.error.Core4SetupError):
        serve(CoreApiTestErrorServer3)


def test_card(http):
    rv = http.get("/core4/api/info?per_page=100")
    assert rv.status_code == 200
    qn = 'tests.api.test_render.InternalHandler1'
    internal_handler = [h for h in rv.json()["data"]
                        if h["qual_name"] == qn]
    pprint(internal_handler)
    assert internal_handler[0]["title"] == "custom title 1"
    assert internal_handler[1]["title"] == "internal test 1"

    c1 = internal_handler[0]["endpoint"][0]["card_url"]
    c0 = internal_handler[1]["endpoint"][0]["card_url"]
    r1 = internal_handler[0]["route_id"]
    r0 = internal_handler[1]["route_id"]

    rv = http.get(c0, absolute=True)
    assert rv.status_code == 200
    content = rv.content.decode('utf-8')
    assert "internal test 1" in content
    assert "tests.api.test_render.InternalHandler1" in content
    assert 'href="/core4/api/enter/' + r0 + '"' in content

    rv = http.get(c1, absolute=True)
    assert rv.status_code == 200
    content = rv.content.decode('utf-8')
    pprint(content)
    assert "custom title 1" in content
    assert "tests.api.test_render.InternalHandler1" in content
    assert 'href="/core4/api/enter/' + r1 + '"' in content



def test_render_relative(http):
    rv = http.get("/test1/render")
    assert rv.status_code == 500

    rv = http.get("/test1/render/relative")
    assert rv.status_code == 200
    assert ("title: rendering handler 1" in rv.content.decode("utf-8"))
    pprint(rv.content)

    css = "/core4/api/file/pro/52b4f9970764d064bb526768b4d8b07c/web/test.css"
    assert css in rv.content.decode("utf-8")
    default = "/core4/api/file/def/52b4f9970764d064bb526768b4d8b07c/default.css"
    assert default in rv.content.decode("utf-8")

    rv = http.get(css)
    assert rv.status_code == 200
    assert "/* web/test.css */" in rv.content.decode("utf-8")

    rv = http.get(default)
    assert rv.status_code == 200
    assert "core4 default css" in rv.content.decode("utf-8")


def test_render_absolute(http):
    rv = http.get("/test1/render/absolute")
    assert rv.status_code == 200
    assert ("title: rendering handler 1" in rv.content.decode("utf-8"))
    pprint(rv.content)
    css = "/core4/api/file/pro/52b4f9970764d064bb526768b4d8b07c/web/test.css"
    assert css in rv.content.decode("utf-8")
    default = "/core4/api/file/def/52b4f9970764d064bb526768b4d8b07c/default.css"
    assert default in rv.content.decode("utf-8")

    rv = http.get(css)
    assert rv.status_code == 200
    assert "/* web/test.css */" in rv.content.decode("utf-8")

    rv = http.get(default)
    assert rv.status_code == 200
    assert "core4 default css" in rv.content.decode("utf-8")


def test_render_path_relative(http):
    rv = http.get("/test1/render2")
    assert rv.status_code == 500

    rv = http.get("/test1/render2/relative")
    assert rv.status_code == 200
    assert "title: rendering handler 2" in rv.content.decode("utf-8")
    assert "web/test1.html" in rv.content.decode("utf-8")
    pprint(rv.content)
    css1 = "/core4/api/file/pro/a0be99aa78cbb87edcba474ddb66718e/test.css"
    assert css1 in rv.content.decode("utf-8")

    css2 = "/core4/api/file/pro/a0be99aa78cbb87edcba474ddb66718e/web/test.css"
    assert css2 in rv.content.decode("utf-8")

    rv = http.get(css1)
    assert rv.status_code == 404

    rv = http.get(css2)
    assert rv.status_code == 200
    assert "/* web/test.css */" in rv.content.decode("utf-8")


def test_render_argument_relative(http):
    rv = http.get("/test1/render2.2")
    assert rv.status_code == 500

    rv = http.get("/test1/render2.2/relative")
    assert rv.status_code == 200
    assert ("custom title render2" in rv.content.decode("utf-8"))

    rv = http.get("/test1/render2.2/absolute")
    assert rv.status_code == 200
    assert ("custom title render2.2" in rv.content.decode("utf-8"))
    pprint(rv.content)
    css = "/core4/api/file/def/d1b13fd5127fa9caa823df81921fbbb0/default.css"
    assert css in rv.content.decode("utf-8")
    rv = http.get(css)
    assert rv.status_code == 200
    assert "core4 default css" in rv.content.decode("utf-8")


def test_static_argument_relative(http):
    rv = http.get("/test1/render2.1/relative")
    assert rv.status_code == 200
    assert ("custom title render2.1" in rv.content.decode("utf-8"))

    rv = http.get("/test1/render2.1/absolute")
    assert rv.status_code == 200
    assert ("custom title render2.1" in rv.content.decode("utf-8"))
    pprint(rv.content)
    css = "/core4/api/file/pro/d68f438f401c76e2039304d3323cd6b2/test1.css"
    assert css in rv.content.decode("utf-8")

    rv = http.get(css)
    assert rv.status_code == 200
    assert "web2/test.css" in rv.content.decode("utf-8")


def test_static_argument_relative(http):
    rv = http.get("/test1/render2.1/relative")
    assert rv.status_code == 200
    assert ("custom title render2.1" in rv.content.decode("utf-8"))

    rv = http.get("/test1/render2.1/absolute")
    assert rv.status_code == 200
    assert ("custom title render2.1" in rv.content.decode("utf-8"))
    pprint(rv.content)
    css = "/core4/api/file/pro/d68f438f401c76e2039304d3323cd6b2/test1.css"
    assert css in rv.content.decode("utf-8")

    rv = http.get(css)
    assert rv.status_code == 200
    assert "web2/test.css" in rv.content.decode("utf-8")


def test_image(http):
    rv = http.get("/test1/render/relative")
    assert rv.status_code == 200
    pprint(rv.content)
    img1 = "/core4/api/file/pro/52b4f9970764d064bb526768b4d8b07c/web/head.png"
    img2 = "/core4/api/file/def/52b4f9970764d064bb526768b4d8b07c/favicon.ico"
    assert img1 in rv.content.decode('utf-8')
    assert img2 in rv.content.decode('utf-8')
    rv = http.get(img1)
    assert rv.status_code == 200
    assert rv.content[
           :20] == b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x01\x00'
    rv = http.get(img2)
    assert rv.status_code == 200
    pprint(rv.content[:20])
    assert rv.content[
           :20] == b'\x00\x00\x01\x00\x03\x00\x10\x10\x00\x00\x01\x00 \x00h\x04\x00\x006\x00'


def test_cage(http):
    rv = http.get("/test1/render3")
    assert rv.status_code == 200
    pprint(rv.content)
    l1 = "/core4/api/file/pro/fa57fc58fe6b34fc5fedf437d832b2ce/test.css"
    l2 = "/core4/api/file/def/fa57fc58fe6b34fc5fedf437d832b2ce/favicon.ico"
    assert l1 in rv.content.decode("utf-8")
    assert l2 in rv.content.decode("utf-8")
    rv = http.get(l1)
    assert rv.status_code == 200
    rv = http.get(l2)
    assert rv.status_code == 200
    l3 = "/core4/api/file/pro/fa57fc58fe6b34fc5fedf437d832b2ce/test1.html"
    rv = http.get(l3)
    assert rv.status_code == 200
    l4 = "/core4/api/file/pro/fa57fc58fe6b34fc5fedf437d832b2ce/../test_render.py"
    rv = http.get(l4)
    assert rv.status_code == 403


if __name__ == '__main__':
    # from core4.api.v1.tool import serve, serve_all
    # serve_all(filter=[
    #     "project.api",
    #     "core4.api.v1.server",
    #     "example"])
    serve(CoreApiTestServer1, CoreApiTestServer2)
