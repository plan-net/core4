from core4.api.v1.application import CoreApiContainer
from core4.api.v1.request.static import CoreStaticFileHandler
from core4.api.v1.request.template import CoreTemplateHandler
from core4.api.v1.tool import serve
from tornado.web import StaticFileHandler

class DemoServer(CoreApiContainer):

    rules = [
        ("/html/(.*)", CoreStaticFileHandler, {"path": "/web/html", "icon": "help"}),
        ("/tmpl(/.*|)", CoreTemplateHandler, {"path": "/web/html", "enter_url": "/demo/tmpl/index.html", "title": "another template handler", "icon": "folder"}),
        ("/link/(.*)", CoreStaticFileHandler, {"path": "/web/html", "icon": "help", "enter_url": "http://www.google.de"}),
    ]


if __name__ == '__main__':
    serve(DemoServer)