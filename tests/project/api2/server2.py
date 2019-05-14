from core4.api.v1.application import CoreApiContainer
from core4.api.v1.request.static import CoreStaticFileHandler
import project.api.request
import project.api.server1

class ProjectServer2(CoreApiContainer):
    root = "/another"
    rules = [
        (r"/req1", project.api.request.TestHandler1),
        (r"/stat2/(.*)", CoreStaticFileHandler, {
            "path": "./html",
            "testvar": "variable hello from ProjectServer2",
            "default_filename": "default.html"
        })
    ]


