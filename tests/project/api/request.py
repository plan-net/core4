from core4.api.v1.request.main import CoreRequestHandler
import core4.util.node

class TestHandler1(CoreRequestHandler):

    def get(self):
        self.reply("OK1")

    def post(self):
        self.reply({"pid": core4.util.node.get_pid()})


class TestHandler2(CoreRequestHandler):

    def get(self):
        self.reply("OK2")