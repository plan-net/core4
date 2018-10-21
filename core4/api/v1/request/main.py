import asyncio

from bson.objectid import ObjectId
from tornado.web import RequestHandler

from core4.base.main import CoreBase


class CoreRequestHandler(CoreBase, RequestHandler):

    def __init__(self, *args, **kwargs):
        CoreBase.__init__(self)
        RequestHandler.__init__(self, *args, **kwargs)

    def prepare(self):
        self.identifier = ObjectId()

    async def run_in_executor(self, meth, *args):
        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(
            self.application.container.executor, meth, *args)
        return await future
