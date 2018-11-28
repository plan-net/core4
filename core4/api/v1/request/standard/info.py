import base64

import core4.service.introspect.api
from core4.api.v1.request.main import CoreRequestHandler


class InfoHandler(CoreRequestHandler):
    title = "API info"
    author = "mra"

    def get(self):
        collection = []
        for (pat, hdlr, *_) in self.application.container.iter_rule():
            rule_name = base64.b16encode(
                bytes(pat, encoding="utf-8")).decode()
            doc = {
                "container": self.application.container.qual_name(),
                "qual_name": hdlr.qual_name(),
                "author": hdlr.author,
                "title": hdlr.title,
                "description": hdlr.__doc__,
                "version": hdlr.version(),
                "card": "%s://%s%s?_xcard=%s" % (
                    self.request.protocol,
                    self.request.host,
                    self.application.container.root,
                    rule_name),
                "help": "%s://%s%s?_xcard=%s&help=1" % (
                    self.request.protocol,
                    self.request.host,
                    self.application.container.root,
                    rule_name),
            }
            collection.append(doc)
        if self.wants_json():
            self.reply(collection)
        else:
            self.render("test.html", collection=collection)
