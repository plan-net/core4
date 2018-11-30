import base64
import hashlib

from core4.api.v1.request.main import CoreRequestHandler

class InfoHandler(CoreRequestHandler):
    title = "API info"
    author = "mra"

    def get(self, qual_name=None):
        if qual_name:
            import core4.service.introspect.api
            inspect = core4.service.introspect.api.CoreApiInspector()
            qual_name = qual_name.split("/")[-1]
            doc = inspect.handler_info(qual_name)
            from pprint import pprint
            pprint(doc)
            return self.render_default(self.help_html_page, doc=doc)
        collection = []
        # container is RootContainer
        for qn, routes in self.application.container.routes.items():
            scope = []
            for md5, data in routes.items():
                app = data["app"]
                (pattern, cls, *args) = data["rule"]
                scope.append({
                    "rule_id": md5,
                    "pattern": pattern,
                    "args": args,
                    "app": app
                })
            scope.sort(key=lambda r: r["pattern"])
            doc = {
                "container": self.application.container.qual_name(),
                "qual_name": cls.qual_name(),
                "author": cls.author,
                "title": cls.title,
                "description": cls.__doc__,
                "version": cls.version(),
                "route": scope,
                "host": self.request.host,
                "protocol": self.request.protocol,
                "project": cls.get_project(),
                # "card": "%s://%s/core4/api/v1/info/%s" % (
                #     self.request.protocol,
                #     self.request.host,
                #     cls.qual_name()),
                # "help": "%s://%s%s?_xcard=%s&help=1" % (
                #     self.request.protocol,
                #     self.request.host,
                #     self.application.container.root,
                #     rule_name),
            }
            collection.append(doc)
        collection = sorted(collection, key=lambda r: r["qual_name"])
        if self.wants_json():
            self.reply(collection)
        else:
            self.render("test.html", collection=collection)
