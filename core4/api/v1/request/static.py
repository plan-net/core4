from bson.objectid import ObjectId
from tornado.web import StaticFileHandler

from core4.base.main import CoreBase

class CoreStaticFileHandler(CoreBase, StaticFileHandler):

    def __init__(self, *args, **kwargs):
        CoreBase.__init__(self)
        StaticFileHandler.__init__(self, *args, **kwargs)

    def prepare(self):
        self.identifier = ObjectId()
