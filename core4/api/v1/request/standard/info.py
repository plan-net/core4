import core4.const
# import core4.service.introspect.api
from core4.api.v1.request.main import CoreRequestHandler
from core4.util.data import unre_url, rst2html


class InfoHandler(CoreRequestHandler):
    title = "endpoint information"
    author = "mra"

    def get(self, ids=None):
        """
        Retrieve API endpoint listing and details for the current tornado
        server.

        Methods:
            GET /info - endpoint listing

        Parameters:
            json (bool): retrieve JSON format, defaults to ``False`` (HTML)

        Returns:
            collection (list) of dict with

            - **project** (*str*): title
            - **version** (*str*): of the project
            - **author** (*str*): of the request handler
            - **qual_name** (*str*): of the endpoint
            - **host** (*str*): name and port
            - **error** (*list*): of parsing error messages from
              :mod:`docutils`
            - **protocol** (*str*): ``http`` or ``https``
            - **description** (*str*): method doc string in HTML format
            - **protected** (*bool*): if the request handler is protected or
              not
            - **route** (*list*): of routes addressing the request handler with

              - **url** (str): pointing to the GET method of the request
                handler
              - **icon** (str): icon label
              - **pattern** (str): for routing
              - **container** (str): :class:`.CoreApiContainer` ``qual_name``
              - **rule_id** (str): rule ID (MD5 digest) of this route
              - **help_url** (str): help endpoint for the request handler
              - **card_url** (str): card page endpoint for the request handler
              - **title** (str): of this route
              - **args** (list): passed to this route of the request handler

        Raises:
            401 Unauthorized:

        Examples:
            >>> from requests import get, post, delete, put
            >>> from pprint import pprint
            >>> import random
            >>> url = "http://localhost:5001/core4/api/v1"
            >>> signin = get(url + "/login?username=admin&password=hans")
            >>> token = signin.json()["data"]["token"]
            >>> h = {"Authorization": "Bearer " + token}
            >>> rv = get("http://localhost:5001/core4/api/v1/info", cookies=signin.cookies)
            >>> rv.json()
            {
                '_id': '5c08c9bcde8b6970b65c0858',
                'code': 200,
                'message': 'OK',
                'timestamp': '2018-12-06T07:03:24.355656',
                'data': {
                    'collection': [
                        {
                            'author': 'mra',
                            'description': '<p>Get job listing, job details, kill, delete and restart jobs.</p>',
                            'error': [],
                            'host': 'localhost:5001',
                            'project': 'core4',
                            'protected': True,
                            'protocol': 'http',
                            'qual_name': 'core4.api.v1.request.queue.job.JobHandler',
                            'route': [
                                {
                                    'args': [],
                                    'card_url': '/core4/api/v1/info/card/3437b1b348dcce91f4949f4d6ad416aa',
                                    'container': 'core4.api.v1.server.CoreApiServer',
                                    'help_url': '/core4/api/v1/info/3437b1b348dcce91f4949f4d6ad416aa',
                                    'icon': 'copyright',
                                    'pattern': '/coco/v1/jobs/?(.*)',
                                    'rule_id': '3437b1b348dcce91f4949f4d6ad416aa',
                                    'title': 'job manager',
                                    'url': '/coco/v1/jobs'
                                }
                            ],
                            'version': '0.0.1'
                        }
                    ]
                }
            }

        Methods:
            GET /info/<rule_id> - endpoint details

        Parameters:
            json (bool): retrieve JSON format, defaults to ``False`` (HTML)

        Returns:
            data element with dict of

            - **project** (*str*): title
            - **version** (*str*): of the project
            - **author** (*str*): of the request handler
            - **qual_name** (*str*): of the endpoint
            - **host** (*str*): name and port
            - **error** (*list*): of parsing error messages from
              :mod:`docutils`
            - **protocol** (*str*): ``http`` or ``https``
            - **description** (*str*): method doc string in HTML format
            - **protected** (*bool*): if the request handler is protected
            - **route** (*list*): of routes addressing the request handler with
            - **method** (*list*): with method details

              - **method** (str): short title
              - **doc** (str): plain RST method doc string
              - **html** (str): method doc string in HTML format
              - **parts** (dict): of bool if the sections **method**,
                **parameter**, **return**, **raise** and **example** exist
              - **extra_parts** (list): of additional sections
              - **parser_error** (list): of parsing erreors

        Raises:
            401 Unauthorized:

        Examples:
            >>> from requests import get, post, delete, put
            >>> from pprint import pprint
            >>> import random
            >>> url = "http://localhost:5001/core4/api/v1"
            >>> signin = get(url + "/login?username=admin&password=hans")
            >>> token = signin.json()["data"]["token"]
            >>> h = {"Authorization": "Bearer " + token}
            >>> rv = get("http://localhost:5001/core4/api/v1/info/e9aebdd95287d83f97f14ce07b4852fd",
            cookies=signin.cookies)
            >>> rv.json()
            {
                '_id': '5c08cbd4de8b6970b66c3c62',
                'code': 200,
                'data': {'args': [],
                         'author': 'mra',
                         'card_url': '/core4/api/v1/info/card/e9aebdd95287d83f97f14ce07b4852fd',
                         'container': 'core4.api.v1.application.RootContainer',
                         'description': '<p>None</p>',
                         'error': [],
                         'help_url': '/core4/api/v1/info/e9aebdd95287d83f97f14ce07b4852fd',
                         'host': 'localhost:5001',
                         'icon': 'copyright',
                         'method': [{
                             'doc': 'stripped for brevity',
                             'extra_parts': [],
                             'html': 'stripped for brevitiy',
                             'method': 'get',
                             'parser_error': [],
                             'parts': {'example': True,
                                       'method': True,
                                       'parameter': True,
                                       'raise': True,
                                       'return': True}}],
                         'pattern': '/core4/api/v1/info/?(.*)',
                         'project': 'core4',
                         'protected': True,
                         'protocol': 'http',
                         'qual_name': 'core4.api.v1.request.standard.info.InfoHandler',
                         'rule_id': 'e9aebdd95287d83f97f14ce07b4852fd',
                         'title': 'endpoint information',
                         'url': '/core4/api/v1/info',
                         'version': '0.0.1'},
                'message': 'OK',
                'timestamp': '2018-12-06T07:12:21.006910'
            }
        """

        def rule_part(container, md5_route, pattern, cls, args):
            if args:
                title = args.pop().get("title", cls.title)
            else:
                title = cls.title
            if args:
                icon = args.pop().get("icon", cls.icon)
            else:
                icon = cls.icon
            return {
                "rule_id": md5_route,
                "pattern": pattern,
                "url": unre_url(pattern),
                "args": args,
                "title": title,
                "icon": icon,
                "container": container.qual_name(),
                "card_url": "%s/%s" % (
                    core4.const.CARD_URL,
                    md5_route
                ),
                "help_url": "%s/%s" % (
                    core4.const.INFO_URL,
                    md5_route
                )
            }

        def handler_part(cls):
            html = rst2html(str(cls.__doc__))
            return {
                "qual_name": cls.qual_name(),
                "author": cls.author,
                "description": html["body"],
                "error": html["error"],
                "version": cls.version(),
                "host": self.request.host,
                "protocol": self.request.protocol,
                "project": cls.get_project(),
                "protected": cls.protected,
            }

        if ids:
            parts = ids.split("/")
            md5_route = parts[0]
            (app, container, pattern, cls, *args) = self.application.find_md5(
                md5_route)
            ret = handler_part(cls)
            ret.update(rule_part(container, md5_route, pattern, cls, args))
            ret["method"] = self.application.handler_help(cls)
            template = "help.html"
        else:
            collection = {}
            # container is RootContainer
            for md5_route, rule in self.application.container.routes.items():
                (app, container, pattern, cls, *args) = rule
                collection.setdefault(
                    cls.qual_name(), {"cls": cls, "route": []})
                collection[cls.qual_name()]["route"].append(
                    (md5_route, app, container, pattern, *args))
            listing = []
            for qual_name in sorted(collection.keys()):
                cls = collection[qual_name]["cls"]
                doc = handler_part(cls)
                doc["route"] = []
                for (md5_route,
                     app,
                     container,
                     pattern,
                     *args) in collection[qual_name]["route"]:
                    rule = rule_part(container, md5_route, pattern, cls, args)
                    doc["route"].append(rule)
                listing.append(doc)
            ret = {"collection": listing}
            template = "widget.html"

        wants_json = self.get_argument("json", as_type=bool, default=False)
        if self.wants_json() or wants_json:
            self.reply(ret)
        else:
            self.render_default(template, **ret)
