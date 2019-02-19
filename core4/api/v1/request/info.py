#This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Implements :class:`.InfoHandler` to retrieve API endpoint details.
"""
from tornado.web import HTTPError

import core4.const
import core4.util.node
from core4.api.v1.request.main import CoreRequestHandler
from core4.util.data import rst2html

class InfoHandler(CoreRequestHandler):
    title = "server endpoint information"
    author = "mra"

    async def enter(self):
        raise HTTPError(400, "You cannot directly enter this endpoint. "
                             "You must provide a route ID to retrieve API "
                             "endpoint help")

    async def get(self, ids):
        """
        Retrieve API endpoint details/help.

        Methods:
            GET /info/<route_id> - endpoint details

        Parameters:
            content_type (str): force json, html, text

        Returns:
            data element with dict of

            - **project** (*str*): title
            - **args** (*dict*): passed from the :class:`.CoreApiContainer` to
              the handler
            - **qual_name** (*str*): of the endpoint
            - **author** (*str*): of the request handler
            - **description** (*str*): method doc string in HTML format
            - **icon** (*str*): material icon
            - **title** (*list*): of the endpoint
            - **pattern** (*list*): of *str* with URL matching pattern
            - **route_id** (*str*): MD5 of the route/pattern
            - **tag** (*list*): of tag strings
            - **container** (*class*): name serving the endpoint
            - **protected** (*bool*): if the request handler is protected
            - **version** (*str*): of the project
            - **error** (*list*): of parsing error messages from
              :mod:`docutils`
            - **card_url** (*str*): URL to card page
            - **enter_url** (*str*): URL to enter
            - **help_url** (*str*): URL to help page
            - **url_name** (*str*): name of the URL to be used in method
              :meth:`.reverse_url`
            - **method** (*list*): with method details

              - **method** (str): ``GET``, ``POST``, ``DELETE``, etc.
              - **doc** (str): plain RST method doc string
              - **html** (str): method doc string in HTML format
              - **parts** (dict): of bool if the sections *method*, *example*,
                *parameter*, *raise*, are defined
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
            >>> rv = get("http://localhost:5001/core4/api/v1/info/8ff1580edf27b12d4231567be936a0d6",
            cookies=signin.cookies)
            >>> rv.json()
        """

        parts = ids.split("/")
        md5_route = parts[0]
        route = self.application.find_md5(md5_route, all=True)
        (app, container, specs) = route[0]
        html = rst2html(str(specs.target.__doc__))
        doc = dict(
            route_id=md5_route,
            args=str(specs.target_kwargs),
            author=specs.target.author,
            container=container.qual_name(),
            description=html["body"],
            error=html["error"],
            icon=specs.target.icon,
            project=specs.target.get_project(),
            protected=specs.target.protected,
            qual_name=specs.target.qual_name(),
            url_name=specs.name or md5_route,
            tag=specs.target.tag,
            title=specs.target.title,
            version=specs.target.version(),
        )
        if specs.target_kwargs:
            for attr in specs.target.propagate:
                if attr in doc:
                    doc[attr] = specs.target_kwargs.get(attr, doc[attr])
        doc["pattern"] = [specs.matcher.regex.pattern for app, container, specs in route]
        doc["help_url"] = core4.const.HELP_URL + "/" + doc["route_id"]
        doc["enter_url"] = core4.const.ENTER_URL + "/" + doc["route_id"]
        doc["card_url"] = core4.const.CARD_URL + "/" + doc["route_id"]
        doc["method"] = self.application.handler_help(specs.target)

        if self.wants_html():
            return self.render("standard/template/help.html", **doc)
        return self.reply(doc)
