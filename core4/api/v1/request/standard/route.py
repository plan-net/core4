import core4.const
from core4.api.v1.request.main import CoreRequestHandler
from core4.util.pager import CorePager

class RouteHandler(CoreRequestHandler):
    title = "core4 api/widget endpoint collection"
    author = "mra"

    # todo: documentation update
    async def get(self):
        """
        Retrieve global API endpoint collection which have been successfully
        visited *recently* by :class:`core.queue.helper.job.ApiJob`.

        Methods:
            GET /info/collection - API endpoint global listing

        Parameters:
            json (bool): retrieve JSON format, defaults to ``False`` (HTML)
            per_page (int): number of elements per page
            page (int): requested page (start counting with 0)
            filter (dict): MongoDB query filter
            sort (list of tuple): with key and sort order

        Returns:
            collection (list) of dict with

            - **_id** (*:class:`bson.objectid.ObjectId`*): MonboDB identifier
            - **project** (*str*): name
            - **args** (*list*): endpoint arguments passed to
              :class:`.CoreApiContainer`
            - **container** (*str*): ``qual_name`` of the
              :class:`.CoreApiContainer`
            - **author** (*str*): of the :class:`.CoreRequestHandler`
            - **pattern** (*str*): of the route including regular expresions
              groups
            - **full_url** (*str*): to the endpoint
            - **card_url** (*str*): to the card page view
            - **help_url** (*str*): to the help page
            - **description** (*str*): doc string
            - **error** (*list*): of :mod:`docutils` parsing errors
            - **host** (*str*): hostname and port
            - **icon** (*str*): Material design icon label
            - **protected** (*bool*): ``True`` if the handler requires
              authentication and authorization
            - **protocol** (*str*): ``http`` or ``https``
            - **qual_name** (*str*): of the :class:`.CoreRequestHandler`
            - **route_id** (*str*): MD5 digest of the route
            - **tag** (*list*): of tag lables assigned to the
              :class:`.CoreRequestHandler`
            - **title** (*str*): of the :class:`.CoreRequestHandler`
            - **url** (*str*): route excluding regular expression groups
            - **version** (*str*): of the project
            - **visited** (*isoformat*): date/time when the
              :class:`core4.queue.helper.job.ApiJob` recently visited the
              endpoint

        Raises:
            401 Unauthorized:

        Examples:
            >>> from requests import get
            >>> url = "http://localhost:5001/core4/api/v1"
            >>> signin = get(url + "/login?username=admin&password=hans")
            >>> token = signin.json()["data"]["token"]
            >>> h = {"Authorization": "Bearer " + token}
            >>> rv = get("http://localhost:5001/core4/api/v1/info/collection?per_page=2", headers=h)
            >>> rv.json()
            {
                '_id': '5c0e7ab4de8b696c96d1b842',
                'timestamp': '2018-12-10T14:39:48.100079',
                'code': 200,
                'message': 'OK',
                'page': 0,
                'count': 2,
                'per_page': 2,
                'page_count': 6,
                'total_count': 12.0,
                'data': [
                    {
                        '_id': '5c0da00a905eedc906935816',
                        'args': [],
                        'author': 'mra',
                        'card_url': '/core4/api/v1/info/card/04e5f7635c0664033f920b028b20ef7a',
                        'container': 'core4.api.v1.application.RootContainer',
                        'description': '<p>None</p>\n',
                        'error': [],
                        'full_url': 'https://mra.devops:8080/core4/api/v1/info/collection',
                        'help_url': '/core4/api/v1/info/04e5f7635c0664033f920b028b20ef7a',
                        'host': 'mra.devops:8080',
                        'icon': 'copyright',
                        'pattern': '/core4/api/v1/info/collection',
                        'project': 'core4',
                        'protected': True,
                        'protocol': 'https',
                        'qual_name': 'core4.api.v1.request.standard.route.RouteHandler',
                        'route_id': '04e5f7635c0664033f920b028b20ef7a',
                        'tag': [],
                        'title': 'core4 api/widget endpoint collection',
                        'url': '/core4/api/v1/info/collection',
                        'version': '0.0.1',
                        'visited': '2018-12-10T10:19:12'
                    },
                    {
                        '_id': '5c0da00a905eedc906935813',
                        'args': [],
                        'author': 'mra',
                        'card_url': '/core4/api/v1/info/card/1baebadac9588d0c3c67e2728f47ee9b',
                        'container': 'core4.api.v1.application.RootContainer',
                        'description': '<p>None</p>\n',
                        'error': [],
                        'full_url': 'https://mra.devops:8080/core4/api/v1/profile',
                        'help_url': '/core4/api/v1/info/1baebadac9588d0c3c67e2728f47ee9b',
                        'host': 'mra.devops:8080',
                        'icon': 'copyright',
                        'pattern': '/core4/api/v1/profile',
                        'project': 'core4',
                        'protected': True,
                        'protocol': 'https',
                        'qual_name': 'core4.api.v1.request.standard.profile.ProfileHandler',
                        'route_id': '1baebadac9588d0c3c67e2728f47ee9b',
                        'tag': [],
                        'title': 'details for the logged in user',
                        'url': '/core4/api/v1/profile',
                        'version': '0.0.1',
                        'visited': '2018-12-10T10:19:12'
                    }
                ]
            }
        """

        per_page = int(self.get_argument("per_page", default=10))
        current_page = int(self.get_argument("page", default=0))
        filter_by = self.get_argument("filter", as_type=dict, default={})
        sort_by = self.get_argument("sort", as_type=list,
                                    default=[("qual_name", 1)])

        coll = self.config.sys.handler.connect_async()
        data = []

        p = {
            "project": 1,
            "tag": 1,
            "route_id": 1,
            "routing": 1,
            "qual_name": 1
        }

        async for doc in coll.find(filter_by, projection=p).sort(sort_by):
            if await self.user.has_api_access(doc["qual_name"]):
                doc["help_url"] = doc["routing"] \
                                  + core4.const.HELP_URL \
                                  + "/" + doc["route_id"]
                doc["enter_url"] = doc["routing"] \
                                   + core4.const.ENTER_URL \
                                   + "/" + doc["route_id"]
                data.append(doc)

        async def _length(filter):
            return len(data)

        async def _query(skip, limit, filter, sort_by):
            return data[skip:skip + limit]

        pager = CorePager(per_page=int(per_page),
                          current_page=int(current_page),
                          length=_length, query=_query)
        page = await pager.page()
        if self.wants_html():
            return self.render("template/route.html", page=page)
        self.reply(page)
