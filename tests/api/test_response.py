from core4.api.v1.application import serve, CoreApiContainer
from core4.api.v1.request.main import CoreRequestHandler
from tests.api.test_job import LocalTestServer, StopHandler, setup


class FlashHandler(CoreRequestHandler):

    def get(self):
        self.flash("INFO", "hello world")
        self.flash("DEBUG", "you 2")
        self.flash_debug("this is %s", "debug")
        self.flash_info("this is info")
        self.flash_warning("this is warning")
        self.flash_error("this is error")
        self.reply([1, 2, 3])


class ErrorHandler(CoreRequestHandler):

    def get(self, variant):
        if variant == "/abort":
            self.abort(409, "this is so not possible")
        raise RuntimeError("this is unexpected")


class MyTestServer(LocalTestServer):
    base_url = "/core4/api/v2"

    def start(self, *args, **kwargs):
        class CoreApiTestServer(CoreApiContainer):
            rules = [
                (r'/kill', StopHandler),
                (r'/flash', FlashHandler),
                (r'/error(/.*)?', ErrorHandler),
            ]

        return CoreApiTestServer


class MyShortTestServer(MyTestServer):

    def serve(self, cls, **kwargs):
        serve(cls, port=self.port, debug=False, **kwargs)


def test_error():
    server = MyTestServer()
    rv = server.get("/xxx")
    assert rv.status_code == 404
    data = rv.json()
    assert data["code"] == 404
    assert data["message"] == "Not Found"
    msg = data["error"].strip()
    assert msg.startswith("Traceback")
    assert msg.endswith("tornado.web.HTTPError: HTTP 404: Not Found")
    server.stop()


def test_error_short():
    server = MyShortTestServer()
    rv = server.get("/xxx")
    assert rv.status_code == 404
    data = rv.json()
    assert data["code"] == 404
    assert data["message"] == "Not Found"
    msg = data["error"].strip()
    assert msg == "http://localhost:5555/core4/api/v2/xxx"
    server.stop()


def test_flash():
    server = MyShortTestServer()
    rv = server.get("/flash")
    assert rv.status_code == 200
    data = rv.json()
    assert data["flash"] == [
        {'level': 'INFO', 'message': 'hello world'},
        {'level': 'DEBUG', 'message': 'you 2'},
        {'level': 'DEBUG', 'message': 'this is debug'},
        {'level': 'INFO', 'message': 'this is info'},
        {'level': 'WARNING', 'message': 'this is warning'},
        {'level': 'ERROR', 'message': 'this is error'}]
    server.stop()


def test_error():
    server = MyShortTestServer()
    rv = server.get("/error")
    data = rv.json()
    assert data["code"] == 500
    assert data["message"] == "Internal Server Error"
    assert data["error"].startswith("RuntimeError: this is unexpected")
    server.stop()


def test_abort():
    server = MyShortTestServer()
    rv = server.get("/error/abort")
    data = rv.json()
    assert data["code"] == 409
    assert data["message"] == "Conflict"
    assert data["error"] == "this is so not possible"
    server.stop()
