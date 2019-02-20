#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import multiprocessing
import requests
import time
from core4.base import CoreBase
from core4.api.v1.application import CoreApiContainer
from core4.api.v1.tool.functool import serve
from core4.api.v1.request.main import CoreRequestHandler
from tornado.ioloop import IOLoop


class StopHandler(CoreRequestHandler):
    protected = False

    def get(self):
        self.logger.warning("stop IOLoop now: %s", IOLoop.current())
        IOLoop.current().stop()


class ClientServer(CoreBase):
    base_url = "/"

    def __init__(self, container, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]
        self.container = container
        self.port = 5555
        self.process = None
        self.process = multiprocessing.Process(target=self.run)
        self.process.start()
        while True:
            try:
                url = self.url("/profile")
                requests.get(url, timeout=1)
                break
            except:
                pass
            time.sleep(1)
        username = self.config.api.admin_username
        password = self.config.api.admin_password
        self.signin = requests.get(
            self.url("/login?username=%s&password=%s" %(username, password)))
        self.token = self.signin.json()["data"]["token"]
        assert self.signin.status_code == 200

    def url(self, url):
        return "http://localhost:{}{}".format(self.port, self.base_url) + url

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

        cls = self.container
        cls.rules.append(
            (r'/kill', StopHandler)
        )
        cls.root = self.base_url
        self.serve(cls)

    def serve(self, cls, **kwargs):
        serve(cls, port=self.port, **kwargs)

    def stop(self):
        rv = self.get("/kill")
        assert rv.status_code == 200
        self.process.join()


if __name__ == '__main__':
    class ApiTest(CoreApiContainer):
        rules = []
    server = ClientServer(ApiTest)