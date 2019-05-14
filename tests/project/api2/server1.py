from core4.api.v1.application import CoreApiContainer
import project.api.request
from core4.api.v1.request.static import CoreStaticFileHandler
import project.api.server2
from core4.api.v1.test import StopHandler

class ProjectServer1(CoreApiContainer):

    rules = [
        (r"/kill", StopHandler),
        (r"/req1", project.api.request.TestHandler1),
        (r"/req2", project.api.request.TestHandler2),
        (r"/stat1/(.*)", CoreStaticFileHandler, {
            "path": "./html",
            "default_filename": "index.html",
            "testvar": "variable hello from ProjectServer1"
        })
    ]

