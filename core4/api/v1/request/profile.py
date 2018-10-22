from core4.api.v1.request.main import CoreRequestHandler


class ProfileHandler(CoreRequestHandler):

    def get(self):
        self.reply("hello world")
