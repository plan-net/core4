import pytest
import tornado
import tornado.simple_httpclient
import tornado.httpserver
import tornado.web
import json
from contextlib import closing
from http.cookies import SimpleCookie
import urllib.parse


class HTTPTestServerClient(tornado.simple_httpclient.SimpleAsyncHTTPClient):
    def initialize(self, *, http_server=None, port=None):
        super().initialize()
        self._http_server = http_server
        self._http_port = port

    def post(self, path, body="", **kwargs):
        return self._fetch("POST", path=path, body=body, **kwargs)

    def put(self, path, body="", **kwargs):
        return self._fetch("PUT", path=path, body=body, **kwargs)

    def get(self, path, **kwargs):
        return self._fetch("GET", path, **kwargs)

    def delete(self, path, **kwargs):
        return self._fetch("DELETE", path=path, **kwargs)

    async def _fetch(self, method, path, **kwargs):
        headers = kwargs.get("headers", {})
        kwargs["headers"] = headers
        if "body" in kwargs:
            body = kwargs["body"]
            if isinstance(body, dict):
                body = json.dumps(body)
            kwargs["body"] = body
        if "json" in kwargs:
            body = kwargs.pop("json")
            body = json.dumps(body)
            headers["Content-Type"] = "application/json"
            kwargs["body"] = body
        req = tornado.httpclient.HTTPRequest(
            self.get_url(path), method=method, **kwargs)
        resp = await super().fetch(req, raise_error=False)
        return self._postproc(resp)

    def _postproc(self, response):

        def _json():
            return json.loads(response.body.decode("utf-8"))

        def _cookie():
            cookie = SimpleCookie()
            s = response.headers.get("set-cookie")
            cookie.load(s)
            return cookie

        response.json = _json
        response.cookie = _cookie
        response.ok = response.code == 200
        return response

    def get_url(self, path):
        p, *q = path.split("?")
        elems = urllib.parse.parse_qs("?".join(q))
        if q:
            p += "?" + urllib.parse.urlencode(elems, doseq=True)
        url = "http://127.0.0.1:%s%s" % (self._http_port, p)
        print(url)
        return url


def run(*app):
    loop = tornado.ioloop.IOLoop().current()
    http_server_port = tornado.testing.bind_unused_port()[1]

    server = tornado.httpserver.HTTPServer(*app)
    server.bind(http_server_port, address="localhost")
    server.start()

    with closing(HTTPTestServerClient(
            http_server=server, port=http_server_port)) as client:
        yield client

    server.stop()

    if hasattr(server, "close_all_connections"):
        loop.run_sync(
            server.close_all_connections
        )
