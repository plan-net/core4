from core4.api.v1.application import CoreApiContainer
import project.api.request
from core4.api.v1.request.static import CoreStaticFileHandler
import project.api.server2
from core4.api.v1.test import StopHandler
from tornado.web import StaticFileHandler
import core4.util.node
from core4.api.v1.request.standard.login import LoginHandler


class MyStatic(CoreStaticFileHandler):

    path = "./html"
    def get_variable(self):
        return {
            "timer": core4.util.node.mongo_now()
        }

class ProjectServer1(CoreApiContainer):

    rules = [
        (r"/kill", StopHandler),
        (r"/req1", project.api.request.TestHandler1),
        (r"/req2", project.api.request.TestHandler2),
        (r"/stat1/(.*)", MyStatic, {
            "default_filename": "index.html",
            "inject": {
                "testvar": "variable hello from ProjectServer1"
            }
        }),
        (r"/classic/(.*)", StaticFileHandler, {
            "path": "./html"
        }),
        (r"/login", LoginHandler),
        (r"/login1", LoginHandler, { "test": "blay<y"}),
    ]

if __name__ == '__main__':
    from core4.api.v1.tool import serve_all
    serve_all("project.api")