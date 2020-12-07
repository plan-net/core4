import json
import os.path
import re

from tornado.web import HTTPError

from core4.api.v1.request.main import CoreRequestHandler


class StoreHandler(CoreRequestHandler):
    """
    This endpoint services a storage in collection ``sys.store``. You can
    configure the entry point into this storage for each user/role individually.
    By defining a permission ``app://store/<path>`` the path element locates
    the document in ``sys.store``.

    Furthermore the *path* is organised hierarchically. All key/value pairs of
    parent documents are inherited down the *path*. A specified key/value pair
    down this path overwrites existing values in parent documents.

    With this layout the application can provide default settings. All users
    without a dedicated ``app:/store/<path`` have access to the root document
    (``id == "/"``).

    Note that access to ``POST``, ``DELETE`` and ``GET`` is supposed to be
    reserved for administrators. Regular users access the endpoint with
    ``PUT``. The default user access permissions to this endpoint is
    ``api://core4.api.v1.request.store.*/u``. There is no default app store
    key. Therefore the root store document is retrieved by default. This is
    equal to an app key ``app://store``.

    **EXAMPLE**::

        # * 1 *
        {
            "_id": "/",
            "hello": "world"
        }

        # * 2 *
        {
            "_id": "/client-1",
            "key": 4711
        }

        # * 3 *
        {
            "_id": "/client-1/team-A",
            "hello": "Europe"
        }

    With this example a user with ``app://store/client-1`` retrieves the
    following document::

        {
            "_id": "/client-1",
            "hello": "world",
            "key": 4711
        }

    A user with ``app://store/client-1/team-A`` retrieves the following
    document::

        {
            "_id": "/client-1/team-A",
            "hello": "Europe",
            "key": 4711
        }

    Finally a user with ``app://store/`` or no app key *store* recieves the
    "default" document::

        {
            "_id": "/",
            "hello": "world"
        }
    """

    author = "mra"
    title = "global user-independent store"
    tag = "api"

    async def post(self, xpath=None):
        """
        create and update a new store document specified by ``xpath``. If no
        ``xpath`` is provided, the root element with ``xpath == "/"`` is
        addressed.

        Methods:
            POST /core4/api/v1/store/<xpath> - create/update a store document

        Parameters:
            xpath (str) - location of the store document
            key/value pairs (dict) - elements to store

        Returns:
            The unmodified store document (dict). Key/value inheritance from
            parent documents is not applied.

        Raises:
            400 Bad Request - failed to parse JSON
            404 Not Found - parent not found

        Examples:
            >>> from requests import post
            >>> rv = post("http://localhost:5001/core4/api/v1/store",
            ...           json={
            ...               "hello": "world"
            ...           }, auth=("admin", "hans"))
            >>> rv
            <Response [200]>
        """
        xpath = self.make_path(xpath)
        try:
            body = self.request.body.decode("utf-8")
            data = json.loads(body)
        except json.JSONDecodeError:
            raise HTTPError(400, "failed to parse JSON")
        parent = xpath.split("/")
        if xpath != "/":
            n = await self.config.sys.store.count_documents(
                {"_id": "/".join(parent[:-1]) or "/"})
            if n == 0:
                raise HTTPError(404, "parent not found")
        await self.config.sys.store.replace_one(
            {"_id": xpath}, data, upsert=True)
        self.logger.info("created store [%s]", xpath)
        self.reply(data)

    async def delete(self, xpath=None):
        """
        remove the store document specified by ``xpath``. If no
        ``xpath`` is provided, the root element with ``xpath == "/"`` is
        addressed.

        Methods:
            DELETE /core4/api/v1/store/<xpath> - remove a store document

        Parameters:
            xpath (str) - location of the store document
            recursive (bool) - recursively remove all child store documents
                (defaults to ``False``)

        Returns:
            list of removed store documents

        Raises:
            400 Bad Request - xpath has children if ``recursive is False``
            400 Bad Request - requires xpath
            404 Not Found - xpath not found

        Examples:
            >>> from requests import delete
            >>> rv = delete("http://localhost:5001/core4/api/v1/store/client-2",
            ...             auth=("admin", "hans"))
            >>> rv
            <Response [200]>
        """
        if xpath is None:
            raise HTTPError(400, "requires xpath")
        recursive = self.get_argument("recursive", as_type=bool, default=False)
        if xpath == "/":
            delpath = "/.+"
        else:
            delpath = xpath + "/.+"
        cur = self.config.sys.store.find({"_id": re.compile(delpath)},
                                         projection=["_id"])
        children = await cur.to_list(None)
        if len(children) != 0 and not recursive:
            raise HTTPError(400, "xpath has [{}] children".format(
                len(children)))
        children = [c["_id"] for c in children]
        children.append(xpath)
        children.sort(reverse=True)
        self.logger.info("delete store %s", ", ".join(children))
        ret = await self.config.sys.store.delete_one({"_id": xpath})
        if ret.deleted_count == 0:
            raise HTTPError(404)
        await self.config.sys.store.delete_many(
            {"_id": re.compile(delpath)})
        self.reply(children)

    async def get(self, xpath=None):
        """
        Retrieve the storage at the specified location. If the client requests
        HTML, then a very simple browser front-end is rendered to support the
        interactive creation, update, deletion and retrieval of documents.

        Methods:
            GET /core4/api/v1/store/<xpath> - retrieve the storage

        Parameters:
            xpath (str) - location of the store

        Returns:
            root (str) - store location
            children (list) - of child documents
            body (dict) - raw data
            inherited - data including key/value pairs from parents

        Raises:
            403 Forbidden

        Examples:
            >>> rv = get("http://localhost:5001/core4/api/v1/store/client-1",
            ...          auth=("admin", "hans"))
            >>> rv
            <Response [200]>
        """
        redirect = self.request.full_url()
        if redirect.endswith("/"):
            return self.redirect(redirect[:-1])
        xpath = self.make_path(xpath)
        if xpath == "/":
            down = '^\/[^\/]+$'
        else:
            down = xpath + "\/[^\/]+$"
        cur = self.config.sys.store.find({"_id": re.compile(down)},
                                         projection=["_id"])
        children = await cur.to_list(None)
        children = [c["_id"] for c in children]
        doc = await self.config.sys.store.find_one({"_id": xpath})
        if doc:
            del doc["_id"]
            rec = await self.parse(xpath)
            del rec["doc"]["_id"]
            inherited = rec["doc"]
        else:
            doc = self.raw_config.store.default
            inherited = []
        if self.wants_html():
            self.render(
                "standard/template/store.html",
                xpath=children,
                root=xpath,
                body=json.dumps(doc),
                inherited=json.dumps(inherited))
        else:
            self.reply({
                "children": children,
                "root": xpath,
                "body": doc,
                "inherited": inherited
            })

    async def put(self, xpath=None):
        """
        This is the public user API interface to the document store. Based on
        the user's app key the entry point into the document store is
        determined and the appropriate store document is returned.

        Methods:
            PUT /core4/api/v1/store - retrieve the user specific store document

        Parameters:
            None

        Returns:
            data (dict) - store document including key/value pairs from parents
            parents (list) - applied parent paths

        Raises:
            405 Not Allowed

        Examples:
            >>> from requests import put
            >>> rv = put("http://localhost:5001/core4/api/v1/store",
            ...          auth=("admin", "hans"))
            >>> rv
            <Response [200]>
        """
        if xpath is None:
            ret = await self.load(self.user)
        else:
            raise HTTPError(405)
        self.reply(ret)

    async def load(self, user):
        xpath = None
        if user is not None:
            for app in await user.casc_perm():
                if app.startswith("app://store"):
                    xpath = app[len("app://store"):]
                    break
        if xpath is None:
            xpath = "/"
        xpath = self.make_path(xpath)
        return await self.parse(xpath)

    async def parse(self, xpath):
        parts = xpath.split("/")
        if xpath == "/":
            parents = [xpath]
        else:
            parents = []
        while xpath != "/":
            parent = "/".join(parts)
            if not parent:
                parent = "/"
            parents.append(parent)
            parts.pop(-1)
            if not parts:
                break
        parents = list(reversed(parents))
        doc = self.raw_config.store.default
        for parent in parents:
            pdoc = await self.config.sys.store.find_one({"_id": parent})
            if pdoc is not None:
                doc.update(pdoc)
        return {"parents": parents, "doc": doc}

    def make_path(self, xpath):
        if xpath is None:
            return "/"
        if not xpath.startswith("/"):
            xpath = "/" + xpath
        return os.path.normpath(xpath)
