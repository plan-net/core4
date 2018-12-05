import core4.const
# import core4.service.introspect.api
from core4.api.v1.request.main import CoreRequestHandler
from core4.util.data import unre_url, rst2html

class InfoHandler(CoreRequestHandler):
    title = "API endpoint information"
    author = "mra"

    def get(self, ids=None):
        """
        Return :class:`.CoreRequestHandler` details for the passed
        ``qual_name`` MD5 digest. The details are assembled by
        :class:`.CoreApiInspector` with

        * ``project``
        * ``qual_name``
        * ``qual_name_id`` (MD5 digest of the ``qual_name``)
        * ``author``
        * ``description``
        * ``host``
        * ``protocol``
        * ``version`` (project)
        * ``routing`` - list of routing patterns delivering the handler, with
          * ``pattern``
          * ``routing_id`` (MD5 digest of the ``pattern``)
          * ``container`` (``qual_name``)
          * ``title`` (as defined by the request handler or argument)
          * ``args``
          * ``card_url``
          * ``help_url``

        :param md5_qual_name: MD5 digest for the request handler ``qual_name``
        :return: dict (see above)
        """

        def rule_part(app, container, md5_qn, md5_route, pattern, cls, args):
            if args:
                title = args.pop().get("title", None)
            else:
                title = cls.title
            return {
                "routing_id": md5_route,
                "pattern": pattern,
                "url": unre_url(pattern),
                "args": args,
                "title": title,
                "container": container.qual_name(),
                "card_url": "%s/%s/%s" % (
                    core4.const.CARD_URL,
                    md5_qn,
                    md5_route
                ),
                "help_url": "%s/%s/%s" % (
                    core4.const.INFO_URL,
                    md5_qn,
                    md5_route
                )
            }

        def handler_part(md5_qn, cls):
            html = rst2html(str(cls.__doc__))
            return {
                "qual_name": cls.qual_name(),
                "qual_name_id": md5_qn,
                "author": cls.author,
                "description": html["body"],
                "error": html["error"],
                "version": cls.version(),
                "host": self.request.host,
                "protocol": self.request.protocol,
                "project": cls.get_project(),
            }

        if ids:
            parts = ids.split("/")
            md5_qn = parts[0]
            md5_route = parts[1]
            (app, container, pattern, cls, *args) = self.application.find_md5(
                md5_qn, md5_route)
            doc = handler_part(md5_qn, cls)
            doc["route"] = rule_part(app, container, md5_qn, md5_route,
                                     pattern, cls, args)
            doc["doc"] = self.application.handler_help(cls)
            return self.reply(doc)
        collection = []
        # container is RootContainer
        for md5_qn, routes in self.application.container.routes.items():
            routing = []
            for md5_route, rule in routes.items():
                (app, container, pattern, cls, *args) = rule
                rule_doc = rule_part(app, container, md5_qn, md5_route,
                                     pattern, cls, args)
                routing.append(rule_doc)
            routing.sort(key=lambda r: r["pattern"])
            doc = handler_part(md5_qn, cls)
            doc["route"] = routing
            collection.append(doc)
        collection = sorted(collection, key=lambda r: r["qual_name"])
        if self.wants_json():
            self.reply(collection)
        else:
            self.render_default("widget.html", collection=collection)
