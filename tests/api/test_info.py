from pprint import pprint

import pytest
from tornado.ioloop import IOLoop

from core4.api.v1.application import CoreApiContainer
from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.request.static import CoreStaticFileHandler
from core4.api.v1.tool.functool import serve
from tests.api.test_render import HttpServer
from tests.api.test_response import setup

_ = setup


class StopHandler(CoreRequestHandler):
    protected = False

    def get(self):
        self.logger.warning("stop IOLoop now: %s", IOLoop.current())
        IOLoop.current().stop()


class StaticTest2(CoreStaticFileHandler):
    path = "static1"
    icon = "help"


class CustomCardHandler1(CoreRequestHandler):

    def card(self):
        self.render("web/card.html")

    def get(self):
        self.reply("welcome from the GET handler")


class ErrorHandler1(CoreRequestHandler):

    def card(self):
        self.render("web/card.html")

    def get(self):
        x = 1 / 0


class LinkHandler1(CoreRequestHandler):
    enter_url = "http://www.google.de"


class CoreApiTestServer1(CoreApiContainer):
    enabled = True
    rules = (
        (r'/kill', StopHandler),
        (r'/static1', CoreStaticFileHandler, {"path": "static1"}),
        (r'/static2', StaticTest2),
        (r'/card1', CustomCardHandler1),
        (r'/error1', ErrorHandler1),
        (r'/link1', LinkHandler1),
    )


# class HttpServer:
#
#     def __init__(self, *args):
#         self.cls = args
#         self.port = 5555
#         self.process = None
#         self.process = multiprocessing.Process(target=self.run)
#         self.process.start()
#         while True:
#             try:
#                 url = self.url("/core4/api/profile")
#                 requests.get(url, timeout=1)
#                 break
#             except:
#                 pass
#             time.sleep(1)
#             tornado.gen.sleep(1)
#         self.signin = requests.get(
#             self.url("/core4/api/login?username=admin&password=hans"))
#         self.token = self.signin.json()["data"]["token"]
#         assert self.signin.status_code == 200
#
#     def url(self, url):
#         return "http://localhost:{}".format(self.port) + url
#
#     def request(self, method, url, **kwargs):
#         if self.token:
#             kwargs.setdefault("headers", {})[
#                 "Authorization"] = "Bearer " + self.token
#         return requests.request(method, self.url(url),
#                                 cookies=self.signin.cookies, **kwargs)
#
#     def get(self, url, **kwargs):
#         return self.request("GET", url, **kwargs)
#
#     def post(self, url, **kwargs):
#         return self.request("POST", url, **kwargs)
#
#     def put(self, url, **kwargs):
#         return self.request("PUT", url, **kwargs)
#
#     def delete(self, url, **kwargs):
#         return self.request("DELETE", url, **kwargs)
#
#     def run(self):
#         serve(*self.cls, port=self.port)
#
#     def stop(self):
#         rv = self.get("/tests/kill")
#         assert rv.status_code == 200
#         self.process.join()


@pytest.fixture()
def http():
    server = HttpServer(CoreApiTestServer1)
    yield server
    server.stop()


def test_server_test(http):
    rv = http.get("/core4/api/profile")
    assert rv.status_code == 200


def test_card(http):
    rv = http.get("/tests/static1")
    assert rv.status_code == 200
    card = "/core4/api/info/card/be596b2d241cbecdc0e59978e678fa6f"
    rv = http.get(card)
    assert rv.status_code == 200


def test_filehandler_card(http):
    rv = http.get("/tests/static1")
    assert rv.status_code == 200
    card = "/core4/api/info/card/be596b2d241cbecdc0e59978e678fa6f"
    rv = http.get(card)
    assert rv.status_code == 200


def test_all_info(http):
    rv = http.get("/core4/api/info")
    assert rv.status_code == 200
    pprint(rv.json())
    data = rv.json()
    for handler in data["data"]:
        for endpoint in handler["endpoint"]:
            rv1 = http.get(endpoint["card_url"], absolute=True)
            assert rv1.status_code == 200
            rv1 = http.get(endpoint["help_url"], absolute=True)
            assert rv1.status_code == 200
        # ign = sum([1 for i in
        #            ("StopHandler", "ErrorHandler1", "LinkHandler1")
        #            if i in handler["qual_name"]])
        # if not ign:
        #     rv1 = http.get(route["enter_url"])
        #     assert rv1.status_code == 200


def test_custom_card(http):
    rv = http.get("/tests/card1")
    assert rv.status_code == 200
    pprint(rv.content)
    card = "/core4/api/info/card/5812647cb9e8ea25678175a04388e30c"
    rv = http.get(card)
    assert rv.status_code == 200


def test_error(http):
    rv = http.get("/tests/error1")
    assert rv.status_code == 500
    pprint(rv.json())
    assert "division by zero" in rv.json()["error"]


def test_link(http):
    rv = http.get("/core4/api/info/card/905e7aaab803d189d0cf661475d5367f")
    assert rv.status_code == 200
    assert '<b>ENTER:</b> <a href="http://www.google.de"' in rv.content.decode(
        "utf-8")


def test_404(http):
    rv = http.get("/core4/api/v1/bla")
    assert rv.status_code == 404
    rv = http.get("/tests/abc")
    assert rv.status_code == 404


if __name__ == '__main__':
    serve(CoreApiTestServer1)
