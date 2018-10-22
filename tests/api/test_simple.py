import pytest
import tornado.routing
import tornado.web


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world!")


@pytest.fixture
def app():
    handlers1 = [
        (r'/app1', MainHandler),
        (r'/app2', MainHandler)
    ]
    rules = []
    for root in ("/test1", "/test2"):
        for h in handlers1:
            rules.append(tornado.routing.Rule(
                tornado.routing.PathMatches(root + h[0]), h[1]))
    app1 = tornado.web.Application(rules)
    app2 = tornado.web.Application(rules)
    routes = [
        tornado.routing.Rule(tornado.routing.PathMatches(
            "/test1.*"), app1),
        tornado.routing.Rule(tornado.routing.PathMatches(
            "/test2.*"), app2)
    ]
    rr = tornado.routing.RuleRouter(routes)
    return rr


async def test_http_server_client(http_server_client):
    resp = await http_server_client.fetch('/test1/app1')
    assert resp.code == 200
    resp = await http_server_client.fetch('/test1/app2')
    assert resp.code == 200
    resp = await http_server_client.fetch('/test2/app1')
    assert resp.code == 200
    resp = await http_server_client.fetch('/test2/app2')
    assert resp.code == 200
