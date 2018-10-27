from bson.objectid import ObjectId
from tornado.web import StaticFileHandler
import time
from core4.api.v1.util import json_encode, json_decode
import jwt
from core4.api.v1.request.main import BaseHandler

class CoreStaticFileHandler(BaseHandler, StaticFileHandler):

    def __init__(self, *args, **kwargs):
        BaseHandler.__init__(self)
        StaticFileHandler.__init__(self, *args, **kwargs)

    def verify_access(self):
        return True


