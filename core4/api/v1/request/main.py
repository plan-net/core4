"""
core4 :class:`.CoreRequestHandler`, based on :class:`.CoreBaseHandler`.
"""
import base64
import os
import traceback

import datetime
import dateutil.parser
import jwt
import mimeparse
import pandas as pd
import time
import tornado.escape
import tornado.httputil
import tornado.template
from bson.objectid import ObjectId
from tornado.web import RequestHandler, HTTPError

import core4.const
import core4.error
import core4.util
import core4.util.node
from core4.api.v1.request.role.model import CoreRole
from core4.base.main import CoreBase
from core4.util.data import parse_boolean, json_encode, json_decode
from core4.util.pager import PageResult

tornado.escape.json_encode = json_encode

FLASH_LEVEL = ("DEBUG", "INFO", "WARNING", "ERROR")


class CoreEtagMixin:

    def compute_etag(self):
        """
        Sets the ``Etag`` header based on static url version.

        See inherited method from :class:`tornado.web.StaticFileHandler`. This
        method skips Etag computation for special endpoints, i.e. ``card`` and
        ``help``.
        """
        if self.absolute_path is None:
            return None
        return super().compute_etag()


class CoreBaseHandler(CoreBase):
    """
    :class:`.CoreRequestHandler` and :class:`.CoreStaticFileHandler` inherit
    from this base class which provides common class properties and methods.
    """
    #: `True` if the handler requires authentication and authorization
    protected = True
    #: handler title
    title = None
    #: handler author
    author = None
    #: tag listing
    tag = []
    #: template path, if not defined use absolute or relative path
    template_path = None
    #: static file path, if not defined use relative path
    static_path = None
    #: link to api/widget (can be overwritten)
    enter_url = None
    #: default material icon
    icon = "copyright"

    upwind = ["log_level", "template_path", "static_path"]

    supported_types = [
        "text/html",
    ]

    def __init__(self, *args, **kwargs):
        """
        Instantiates the handler and sets error, card and help sources.
        """
        super().__init__()

        def rel(path):
            return "file://" + os.path.abspath(
                os.path.join(os.path.dirname(__file__), path))

        self.error_html_page = rel(self.config.api.error_html_page)
        self.error_text_page = rel(self.config.api.error_text_page)
        self.card_html_page = rel(self.config.api.card_html_page)
        self.help_html_page = rel(self.config.api.help_html_page)
        self.started = core4.util.node.mongo_now()
        self._flash = []
        self.user = None

    def propagate_property(self, source, kwargs):
        """
        Merge the attributes ``protected``, ``title``, ``author``, ``tag``,
        ``template_path``, ``static_path``, ``enter_url`` and ``icon``
        from the passed class/object (``source`` parameter) and ``kwargs``.

        :param source: class or object based on :class:`.CoreRequestHandler` or
            :class:`.CoreStaticFileHandler`
        :param kwargs: arguments based as ``rules`` by
            :class:`.CoreApiContainer`
        :return: yield attribute name and value
        """
        for attr in ("protected", "title", "author", "tag", "template_path",
                     "static_path", "enter_url", "icon"):
            val = kwargs.get(attr, None)
            if val is None:
                yield attr, getattr(source, attr)
            else:
                yield attr, val

    async def options(self, *args, **kwargs):
        """
        Answer preflight / OPTIONS request with ``OK 200``
        """
        self.finish()

    def set_default_headers(self):
        """
        Set the default HTTP headers to allow CORS, see core4 config setting
        `api.allow_origin`. This method allows all methods ``GET``, ``POST``,
        ``PUT``, ``DELETE``, and ``OPTIONS``.
        """
        self.set_header("access-control-allow-origin",
                        self.config.api.allow_origin)
        self.set_header("Access-Control-Allow-Headers",
                        "x-requested-with")
        self.set_header('Access-Control-Allow-Methods',
                        'GET, POST, PUT, DELETE, OPTIONS')
        self.set_header(
            "Access-Control-Allow-Headers",
            "access-control-allow-origin,authorization,content-type")

    async def prepare(self):
        """
        Prepares the handler with

        * setting the request ``.identifier``
        * authentication and authorization

        Raises 401 error if authentication and authorization fails.
        """
        self.identifier = ObjectId()
        if self.request.method in ('OPTIONS'):
            # preflight / OPTIONS should always pass
            return
        await self.prepare_protection()

    async def prepare_protection(self):
        """
        This is the authentication and authorization part of :meth:`.prepare`
        and sets the ``.current_user`` (name) and ``.user`` (object).

        Raises ``401 - Unauthorized``.
        """
        if self.protected:
            user = await self.verify_user()
            if user:
                self.current_user = user.name
                self.user = user
                if await self.verify_access():
                    return
            raise HTTPError(401)

    async def verify_access(self):
        """
        Verifies the user/role has access to the resource.

        :return: ``True`` or ``False``
        """
        return True

    async def verify_user(self):
        """
        Extracts client's authorization from

        #. Basic Authorization header, or from
        #. Bearer Authorization header, or from
        #. token parameter (query string or json body), or from
        #. token parameter from the cookie, or from
        #. passed username and password parameters (query string or json body)

        In case a valid username and password is provided, the token is
        created, see :meth:`.create_token`.

        If the creation time of the token is older than 1h, then a refresh
        token is created and sent with the HTTP header (field ``token``).
        This refresh time can be configured with setting ``api.token.refresh``.

        :return: verified username
        """
        auth_header = self.request.headers.get('Authorization')
        username = password = None
        token = None
        source = None
        if auth_header is not None:
            auth_type = auth_header.split()[0].lower()
            if auth_type == "basic":
                auth_decoded = base64.decodebytes(
                    auth_header[6:].encode("utf-8"))
                username, password = auth_decoded.decode(
                    "utf-8").split(':', 2)
                source = ("username", "Auth Basic")
            elif auth_type == "bearer":
                token = auth_header[7:]
                source = ("token", "Auth Bearer")
        else:
            token = self.get_argument("token", default=None)
            username = self.get_argument("username", default=None)
            password = self.get_argument("password", default=None)
            if token is not None:
                source = ("token", "args")
            elif username and password:
                source = ("username", "args")
            else:
                source = ("token", "cookie")
                token = self.get_secure_cookie("token")
        if token:
            payload = self.parse_token(token)
            username = payload.get("name")
            if username:
                user = await CoreRole().find_one(name=username)
                if user is None:
                    self.logger.warning(
                        "failed to load [%s] by [%s] from [%s]", username,
                        *source)
                else:
                    self.token_exp = datetime.datetime.fromtimestamp(
                        payload["exp"])
                    renew = self.config.api.token.refresh
                    if (core4.util.node.now()
                        - datetime.datetime.fromtimestamp(
                                payload["timestamp"])).total_seconds() > renew:
                        self.create_token(username)
                        self.logger.debug("refresh token [%s] to [%s]",
                                          username, self.token_exp)
                    self.logger.debug(
                        "successfully loaded [%s] by [%s] from [%s] "
                        "expiring [%s]", username, *source, self.token_exp)
                    return user
        elif username and password:
            try:
                user = await CoreRole().find_one(name=username)
            except:
                self.logger.warning(
                    "failed to load [%s] by [%s] from [%s]", username, *source)
            else:
                if user and user.verify_password(password):
                    self.token_exp = None
                    self.logger.debug(
                        "successfully loaded [%s] by [%s] from [%s]",
                        username, *source)
                    await user.login()
                    return user
        return None

    def create_token(self, username):
        """
        Creates the authorization token using JSON web tokens (see :mod:`jwt`)
        and sets the required headers and cookie. The token expiration time can
        be set with core4 config key ``api.token.expiration``.

        :param username: to be packaged into the web token
        :return: JSON web token (str)
        """
        secs = self.config.api.token.expiration
        payload = {
            'name': username,
            'timestamp': core4.util.node.now().timestamp()
        }
        token = self.create_jwt(secs, payload)
        self.set_secure_cookie("token", token)
        self.set_header("token", token)
        self.logger.debug("updated token [%s]", username)
        return token

    def create_jwt(self, secs, payload):
        """
        Creates the JSON web token using the passed expiration time in seconds
        and the ``payload``.

        :param secs: JWT expiration time (in seconds)
        :param payload: JWT payload
        :return: JWT (str)
        """
        self.logger.debug("set token lifetime to [%d]", secs)
        expires = datetime.timedelta(
            seconds=secs)
        secret = self.config.api.token.secret
        algorithm = self.config.api.token.algorithm
        self.token_exp = (core4.util.node.now()
                          + expires).replace(microsecond=0)
        payload["exp"] = self.token_exp
        token = jwt.encode(payload, secret, algorithm)
        return token.decode("utf-8")

    def parse_token(self, token):
        """
        Parses the passed JSON web token.

        This method raises :class:`jwg.ExpiredSignatureError` if the JWT is
        invalid.

        :param token: JWT (str)
        :return: decoded JWT payload
        """
        secret = self.config.api.token.secret
        algorithm = self.config.api.token.algorithm
        try:
            return jwt.decode(token, key=secret, algorithms=[algorithm],
                              verify=True)
        except jwt.InvalidSignatureError:
            raise HTTPError("signature verification failed")
        except jwt.ExpiredSignatureError:
            return {}

    def log_exception(self, typ, value, tb):
        """
        Override to customize logging of uncaught exceptions.

        By default logs instances of `HTTPError` as warnings without
        stack traces (on the ``tornado.general`` logger), and all
        other exceptions as errors with stack traces (on the
        ``tornado.application`` logger).
        """
        if isinstance(value, HTTPError):
            if value.status_code < 500:
                logger = self.logger.warning
            else:
                logger = self.logger.error
            logger(
                "\n".join(traceback.format_exception_only(typ, value)).strip()
            )
        else:
            self.logger.error(
                "%s\n%s",
                "\n".join(traceback.format_exception_only(typ, value)).strip(),
                "\n".join(traceback.format_tb(tb))
            )

    def xcard(self, *args, **kwargs):
        """
        Prepares the ``card`` page and triggers :meth:`.card` which is to be
        overwritten for custom widget card implementations.

        :return: result of :meth:`.card`
        """
        self.request.method = "GET"
        parts = self.request.path.split("/")
        md5_route_id = parts[-1]
        self.absolute_path = None
        if self.enter_url is None:
            self.enter_url = "/".join([core4.const.ENTER_URL, md5_route_id])
        self.help_url = "/".join([core4.const.HELP_URL, md5_route_id])
        return self.card()

    def card(self):
        """
        Renders the default card page. This method is to be overwritten for
        custom card page impelementation.
        """
        return self.render(self.card_html_page)

    def get_template_path(self):
        """
        Returns the template path for the handler as defined by property
        ``.template_path``.

        :return: absolute path name of the template directory
        """
        return self.template_path

    def render_string(self, template_name, **kwargs):
        """
        Generate the given template with the given arguments.

        The method is internally used by :meth:'.render` and overwrites the
        original method :meth:`tornado.web.RequestHandler.render_string`.

        This method introduces two special processes before the original method
        is spawned. First, the method handles all templates prefixed with
        ``file://`` as absolute path names. Second, the method differentiates
        templates with and without a leading slash (``/``). A leading slash
        addresses templates from the root path of the project (absolute paths).
        Relative paths address tempaltes in the specified template folder. See
        :meth:`.set_path` about this template folder.

        :param template_name: file name
        :param kwargs: variables to be injected
        :return:
        """
        if template_name.startswith("file://"):
            template_name = template_name[len("file://"):]
            (dirname, filename) = os.path.split(template_name)
            self.template_path = dirname
            template_name = filename
        else:
            (dirname, filename) = os.path.split(template_name)
            if template_name.startswith("/"):
                self.template_path = self.project_path()
                template_name = template_name[1:]
            else:
                path = self.set_path("template_path",
                                     self.application.container)
                self.template_path = os.path.join(path, dirname)
                template_name = filename
        self.logger.debug("template_path is [%s]", self.template_path)
        return super().render_string(template_name, **kwargs)

    def _url(self, mode, path, include_host):
        """
        Build urls to :class:`.CoreFileHandler` to serve static files.

        :param mode: ``def`` for default folder and ``rel`` for relative paths
        :param path: name
        :param include_host: adds the hostname and port if ``True``
        :return: full url
        """
        prefix = ""
        if include_host:
            prefix = "%s://%s" % (self.request.protocol, self.request.host)
        if not path.startswith("/"):
            path = "/" + path
        return "".join([prefix, core4.const.FILE_URL, "/" + mode + "/",
                        self.route_id(), path])

    def default_static(self, path, include_host=None):
        """
        Build urls to core4 default static folder. The method is in scope of
        the templating namespace.


        :param path: name
        :param include_host: adds the hostname and port if ``True``
        :return: full url
        """
        return self._url("def", path, include_host)

    def static_url(self, path, include_host=None, **kwargs):
        """
        Translates the static URL into a route for :class:`.CoreFileHandler`.
        The method is in scope of the templating namespace.

        Method behavior depends on the :attr:`static_path` setting set as a
        class property or passed to :class:`.CoreApiContainer` (see
        :meth:`propagate_property`). If no :attr:`static_path`  is set, then
        a relative path addresses a static file relative to the location of the
        module of the request handler. If the :attr:`static_path` is defined,
        then the relative path addresses a static file relative to this folder.

        :param path: static file
        :param include_host: adds the hostname and port if ``True``
        :param kwargs:
        :return: full url
        """
        return self._url("pro", path, include_host)

    def get_template_namespace(self):
        """
        Extends the templating namespace with :meth:`.default_static`.

        :return: namespace dict
        """
        namespace = super().get_template_namespace()
        namespace["default_static"] = self.default_static
        return namespace

    def route_id(self):
        """
        Identifies the ``route_id`` by the route pattern of the resource.

        :return: ``route_id``
        """
        for rule in self.application.wildcard_router.rules:
            route = rule.matcher.match(self.request)
            if route is not None:
                return rule.name
        return None

    def write_error(self, status_code, **kwargs):
        """
        Write and finish the request/response cycle with error.

        :param status_code: valid HTTP status code
        :param exc_info: Python exception object
        """
        self.set_status(status_code)
        var = {
            "code": status_code,
            "message": tornado.httputil.responses[status_code],
            "_id": self.identifier,
        }
        if "exc_info" in kwargs:
            error = traceback.format_exception_only(*kwargs["exc_info"][0:2])
            if self.settings.get("serve_traceback"):
                error += traceback.format_tb(kwargs["exc_info"][2])
            var["error"] = "\n".join(error)
        elif "error" in kwargs:
            var["error"] = kwargs["error"]
        ret = self._build_json(**var)
        if self.wants_json():
            self.finish(ret)
        elif self.wants_html():
            ret["contact"] = self.config.api.contact
            self.render(self.error_html_page, **ret)
        elif self.wants_text() or self.wants_csv():
            self.render(self.error_text_page, **var)

    def _build_json(self, message, code, **kwargs):
        # internal method to wrap the response
        ret = {
            "_id": self.identifier,
            "timestamp": core4.util.node.now(),
            "message": message,
            "code": code
        }
        for extra in ("error", "data"):
            if extra in kwargs:
                ret[extra] = kwargs[extra]
        if self._flash:
            ret["flash"] = self._flash
        return ret

    def _wants(self, value, set_content=True):
        # internal method to very the client's accept header
        expect = self.guess_content_type() == value
        if expect and set_content:
            self.set_header("Content-Type", value + "; charset=UTF-8")
        return expect

    def wants_json(self):
        """
        Tests the client's ``Accept`` header for ``application/json`` and
        sets the corresponding response ``Content-Type``.

        :return: ``True`` if best guess is JSON
        """
        return self._wants("application/json")

    def wants_html(self):
        """
        Tests the client's ``Accept`` header for ``text/html`` and
        sets the corresponding response ``Content-Type``.

        :return: ``True`` if best guess is HTML
        """
        return self._wants("text/html")

    def wants_text(self):
        """
        Tests the client's ``Accept`` header for ``text/plain`` and
        sets the corresponding response ``Content-Type``.

        :return: ``True`` if best guess is plain text
        """
        return self._wants("text/plain")

    def wants_csv(self):
        """
        Tests the client's ``Accept`` header for ``text/csv`` and
        sets the corresponding response ``Content-Type``.

        :return: ``True`` if best guess is CSV
        """
        return self._wants("text/csv")

    def guess_content_type(self):
        """
        Guesses the client's ``Accept`` header using :mod:`mimeparse` against
        the supported :attr:`.supported_types`.

        :return: best match (str)
        """
        return mimeparse.best_match(
            self.supported_types, self.request.headers.get("accept", ""))


class CoreRequestHandler(CoreBaseHandler, RequestHandler):
    """
    The base class to all custom core4 API request handlers. Typically you
    inherit from this class to implement ReST API request handlers::

        class TestHandler(CoreRequestHandler):

            def get(self):
                return self.reply("hello world")
    """

    SUPPORTED_METHODS = ("GET", "HEAD", "POST", "DELETE", "PATCH", "PUT",
                         "OPTIONS", "XCARD", "XHELP")

    supported_types = [
        "text/html",
        "text/plain",
        "text/csv",
        "application/json"
    ]

    def __init__(self, *args, **kwargs):
        """
        Instantiation of request handlers passes all ``*args`` and ``**kwargs``
        to :class:`.CoreBaseHandler` and :mod:`tornado` handler instantiation
        method.
        """
        CoreBaseHandler.__init__(self, *args, **kwargs)
        RequestHandler.__init__(self, *args, **kwargs)

    def initialize(self, *args, **kwargs):
        """Hook for subclass initialization called for each request.

        The following keywords represent special ``**kwargs`` and overwrite
        :class:`.CoreRequestHandler` class properties. See
        :meth:`.propagate_property`.

        * ``protected`` - authentication/authorization required
        * ``title`` - api/widget title
        * ``author`` - author
        * ``tag`` - list of tags
        * ``template_path`` - absolte from project root, relative from request
        * ``static_path`` - absolute from project root, relative from request
        * ``enter_url`` - custom target url
        * ``icon`` - material icon
        """
        for attr, value in self.propagate_property(self, kwargs):
            self.__dict__[attr] = value

    @classmethod
    def set_path(cls, key, container, **kwargs):
        """
        Class method to identify the handler's ``template_path`` and
        ``static_path`` setting.

        The method searches the corresponding arguments passed to
        :class:`.CoreApiContainer` for the handler, i.e. the passed ``key``
        (``template_path`` or ``static_path``). An absolute path argument
        addresses a folder from the project root. A relative path argument
        addresses the handler's module directory or the
        :class:`.CoreApiContainer` module directory if the handler is not
        inheriting from core4 but directly located in the container.

        This rather complex explanation is best explained with some examples.

        **relative path from :class:`.CoreRequestHandler`**::

            class TestHandler(CoreRequestHandler):

                def get(self):
                    self.render("templates/test.html")


            class CoreApiTestServer1(CoreApiContainer):
                rules = (
                    (r'/example', TestHandler)
                )

        In this example, the file ``templates/test.html`` is to be located
        relative to the the request handler ``TestHandler``.

        **relative path from ``template_path``**::

            class TestHandler(CoreRequestHandler):

                template_path = "templates"

                def get(self):
                    self.render("test.html")


            class CoreApiTestServer1(CoreApiContainer):
                rules = (
                    (r'/example', TestHandler)
                )

        In this example, the file ``test.html`` is to be located relative to
        the handler's ``template_path``. The ``template_path`` is located
        relative to the request handler ``TestHandler`` location.

        **relative path from project root**::

            class TestHandler(CoreRequestHandler):

                template_path = "/api/templates"

                def get(self):
                    self.render("test.html")


            class CoreApiTestServer1(CoreApiContainer):
                rules = (
                    (r'/example', TestHandler)
                )

        In this example, the file ``test.html`` is to be located relative to
        directory ``api/templates``. This ``template_path`` is at
        ``<project>/api/templates`` from the project root.

        **relative path from :class:`.CoreApiContainer**::

            class CoreApiTestServer1(CoreApiContainer):
                rules = (
                    (r'/example', TestHandler,
                     {"template_path": "/api/templates2"})
                )

        In this example, the ``template_path`` argument overwrites the
        variable set by ``TestHandler``. The template file ``test.html`` is to
        be located relative to ``<project>/api/templates2`` from the project
        root.

        :param key: ``template_path`` or ``static_path``
        :param container: :class:`.CoreApiContainer` of the handler
        :param kwargs: handler arguments passed to the
            :class:`.CoreApiContainer`
        :return: full path name
        """
        # get from handler argument or handler class
        for value in (kwargs.get(key, None), getattr(cls, key)):
            base = value
            if base is not None:
                break
        if base is not None:
            if base.startswith("/"):
                root = cls.project_path()
                base = base[1:]
            else:
                if cls.project == core4.const.CORE4:
                    root = container.pathname()
                else:
                    root = cls.pathname()
            path = os.path.join(root, base)
        else:
            path = cls.pathname()
        return path

    async def prepare(self):
        """
        Prepares the handler with

        * setting the ``request_id``
        * preparing the combined parsing of query and body arguments
        * authenticates and authorizes the user

        Raises 401 error if authentication and authorization fails.
        """
        await super().prepare()
        if self.request.body:
            try:
                body_arguments = json_decode(self.request.body.decode("UTF-8"))
            except:
                pass
            else:
                for k, v in body_arguments.items():
                    self.request.arguments.setdefault(k, []).append(v)

    def decode_argument(self, value, name=None):
        """
        Decodes bytes and str from the request.

        The name of the argument is provided if known, but may be None
        (e.g. for unnamed groups in the url regex).
        """
        if isinstance(value, (bytes, str)):
            return super().decode_argument(value, name)
        return value

    def get_argument(self, name, as_type=None, *args, **kwargs):
        """
        Returns the value of the argument with the given name.

        If default is not provided, the argument is considered to be
        required, and we raise a `MissingArgumentError` if it is missing.

        If the argument appears in the url more than once, we return the
        last value.

        If ``as_type`` is provided, then the variable type is converted. The
        method supports the following variable types:

        * int
        * float
        * bool - using :meth:`parse_boolean <core4.util.data.parse_boolean>`
        * str
        * dict - using :mod:`json.loads`
        * list - using :mod:`json.loads`
        * datetime - using :meth:`dateutil.parser.parse`

        :param name: variable name
        :param default: value
        :param as_type: Python variable type
        :return: value
        """
        kwargs["default"] = kwargs.get("default", self._ARG_DEFAULT)
        ret = self._get_argument(name, source=self.request.arguments,
                                 *args, strip=False, **kwargs)
        if as_type and ret is not None:
            try:
                if as_type == bool:
                    if isinstance(ret, bool):
                        return ret
                    return parse_boolean(ret, error=True)
                if as_type == dict:
                    if isinstance(ret, dict):
                        return ret
                    return json_decode(ret)
                if as_type == list:
                    if isinstance(ret, list):
                        return ret
                    return json_decode(ret)
                if as_type == datetime.datetime:
                    if isinstance(ret, datetime.datetime):
                        dt = ret
                    else:
                        dt = dateutil.parser.parse(ret)
                    if dt.tzinfo is None:
                        return dt
                    utc_struct_time = time.gmtime(time.mktime(dt.timetuple()))
                    return datetime.datetime.fromtimestamp(
                        time.mktime(utc_struct_time))
                if as_type == ObjectId:
                    if isinstance(ret, ObjectId):
                        return ret
                    return ObjectId(ret)
                return as_type(ret)
            except:
                raise core4.error.ArgumentParsingError(
                    "parameter [%s] expected as_type [%s]", name,
                    as_type.__name__) from None
        return ret

    async def verify_access(self):
        """
        Verifies the user has access to the handler using
        :meth:`User.has_api_access`.

        :return: ``True`` for success, else ``False``
        """
        if self.user and await self.user.has_api_access(self.qual_name()):
            return True
        return False

    def reply(self, chunk):
        """
        Wraps Tornado's ``.write`` method and finishes the request/response
        cycle featuring the content types :class:`pandas.DataFrame`,
        Python dict and Python str.

        :param chunk: :class:`pandas.DataFrame`, Python dict or str
        :return: str
        """
        if isinstance(chunk, pd.DataFrame):
            if self.wants_csv():
                chunk = chunk.to_csv(encoding="utf-8")
            elif self.wants_html():
                chunk = chunk.to_html()
            elif self.wants_text():
                chunk = chunk.to_string()
            else:
                chunk = chunk.to_dict('rec')
        elif isinstance(chunk, PageResult):
            page = self._build_json(
                code=self.get_status(),
                message=self._reason,
                data=chunk.body,
            )
            page["page_count"] = chunk.page_count
            page["total_count"] = chunk.total_count
            page["page"] = chunk.page
            page["per_page"] = chunk.per_page
            page["count"] = chunk.count
            self.finish(page)
            return
        elif isinstance(chunk, (dict, list)) or self.wants_json():
            pass
        chunk = self._build_json(
            code=self.get_status(),
            message=self._reason,
            data=chunk
        )
        self.finish(chunk)

    def flash(self, level, message, *vars):
        """
        Add a flash message with

        :param level: DEBUG, INFO, WARNING or ERROR
        :param message: str to flash
        """
        level = level.upper().strip()
        assert level in FLASH_LEVEL
        self._flash.append({"level": level, "message": message % vars})

    def flash_debug(self, message, *vars):
        """
        Add a DEBUG flash message.

        :param message: str.
        :param vars: optional str template variables
        """
        self.flash("DEBUG", message % vars)

    def flash_info(self, message, *vars):
        """
        Add a INFO flash message.

        :param message: str.
        :param vars: optional str template variables
        """
        self.flash("INFO", message % vars)

    def flash_warning(self, message, *vars):
        """
        Add a WARNING flash message.

        :param message: str.
        :param vars: optional str template variables
        """
        self.flash("WARNING", message % vars)

    def flash_error(self, message, *vars):
        """
        Add a ERROR flash message.

        :param message: str.
        :param vars: optional str template variables
        """
        self.flash("ERROR", message % vars)

    def parse_objectid(self, _id):
        """
        Helper method to translate a str into a
        :class:`bson.objectid.ObjectId`.

        Raises ``400 - Bad Request``

        :param _id: str to parse
        :return: :class:`bson.objectid.ObjectId`
        """
        try:
            return ObjectId(_id)
        except:
            raise HTTPError(400, "failed to parse ObjectId [%s]", _id)
