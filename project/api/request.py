from core4.api.v1.request.main import CoreRequestHandler


class TestHandler1(CoreRequestHandler):

    def get(self):
        self.reply("OK1")


class TestHandler2(CoreRequestHandler):

    def get(self):
        self.reply("OK2")