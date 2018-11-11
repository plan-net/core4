import asyncio
import base64
import traceback

import datetime
import dateutil.parser
import jwt
import mimeparse
import pandas as pd
import time
import tornado.escape
import tornado.httputil
from bson.objectid import ObjectId
from tornado.web import RequestHandler, HTTPError

import core4.error
import core4.util
import core4.util.node
from core4.api.v1.request.role.model import CoreRole
from core4.api.v1.util import json_encode, json_decode
from core4.base.main import CoreBase
from core4.util.data import parse_boolean
from core4.util.pager import PageResult

tornado.escape.json_encode = json_encode

FLASH_LEVEL = ("DEBUG", "INFO", "WARNING", "ERROR")


class BaseHandler(CoreBase):
    """
    Base class of :class:`.CoreRequestHandler` and
    :class:`.CoreStaticFileHandler`.
    """

    #: `True` if the handler requires authentication and authorization
    protected = True
    #: handler title
    title = None
    #: handler author
    author = None
    #: handler description
    description = None

    async def options(self):
        """
        Answer preflight / OPTIONS request with 200
        """
        # self.set_status(200)
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

        * setting the ``request_id``
        * preparing the combined parsing of query and body arguments
        * authenticates and authorizes the user

        Raises 401 error if authentication and authorization fails.
        """
        self.identifier = ObjectId()
        if (self.request.method == 'OPTIONS'):
            # preflight / OPTIONS should always pass
            return
        # if not (self.request.query_arguments or self.request.body_arguments):
        #     if self.request.body:
        #         body_arguments = json_decode(self.request.body.decode("UTF-8"))
        #         for k, v in body_arguments.items():
        #             self.request.arguments.setdefault(k, []).append(v)
        if self.request.body:
            body_arguments = json_decode(self.request.body.decode("UTF-8"))
            for k, v in body_arguments.items():
                self.request.arguments.setdefault(k, []).append(v)
        if self.protected:
            user = await self.verify_user()
            if user:
                self.current_user = user.name
                if await self.verify_access():
                    return
            self.write_error(401)

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
            user = await CoreRole().find_one(name=username)
            if user is None:
                self.logger.warning(
                    "failed to load [%s] by [%s] from [%s]", username, *source)
            else:
                self.token_exp = datetime.datetime.fromtimestamp(
                    payload["exp"])
                renew = self.config.api.token.refresh
                if (core4.util.node.now()
                    - datetime.datetime.fromtimestamp(
                            payload["timestamp"])).total_seconds() > renew:
                    self.create_token(username)
                    self.logger.debug("refresh token [%s] to [%s]", username,
                                      self.token_exp)
                self.logger.debug(
                    "successfully loaded [%s] by [%s] from [%s] expiring [%s]",
                    username, *source, self.token_exp)
                return user
        elif username and password:
            try:
                user = await CoreRole().find_one(name=username)
            except:
                self.logger.warning(
                    "failed to load [%s] by [%s] from [%s]", username, *source)
            else:
                if user.verify_password(password):
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

    async def verify_access(self):
        """
        Verifies the user has access to the resource. This method requires
        implementation
        """
        raise NotImplementedError


class CoreRequestHandler(BaseHandler, RequestHandler):
    """
    The base class to all custom core4 API request handlers. Typically you
    inherit from this class to implement request handlers::

        class TestHandler(CoreRequestHandler):

            def get(self):
                return "hello world"
    """
    #: this class supports the following content types
    supported_types = [
        "text/html",
        "text/plain",
        "text/csv",
        "application/json"
    ]

    def __init__(self, *args, **kwargs):
        BaseHandler.__init__(self)
        RequestHandler.__init__(self, *args, **kwargs)
        self.error_html_page = self.config.api.error_html_page
        self.error_text_page = self.config.api.error_text_page
        self._flash = []

    async def verify_access(self):
        """
        Verifies the user has access to the handler using
        :meth:`User.has_api_access`.

        :return: ``True`` for success, else ``False``
        """
        try:
            # todo: do we really want to load the role 2x
            user = await CoreRole().find_one(name=self.current_user)
        except:
            self.logger.warning("username [%s] not found", self.current_user)
        else:
            if await user.has_api_access(self.qual_name()):
                return True
        return False

    async def run_in_executor(self, meth, *args):
        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(
            self.application.container.executor, meth, *args)
        return await future

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

    # def abort(self, status_code, message=None, exc_info=False):
    #     """
    #     Abort the request/response cycle with an error. Raises
    #     :class:`tornado.web.HTTPError`.
    #
    #     :param status_code: valid HTTP status code
    #     :param message: additional message
    #     :param exc_info: pass exception info as message if ``True``
    #     """
    #     if exc_info:
    #         exc = "---".join(
    #             traceback.format_exception_only(*sys.exc_info()[0:2]))
    #         self.write_error(status_code, error=exc)
    #         raise HTTPError(status_code, "Abort: %s" % exc)
    #     else:
    #         self.write_error(status_code, error=message)
    #         raise HTTPError(status_code, "Abort: %s" % message)

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

    def parse_objectid(self, _id):
        try:
            return ObjectId(_id)
        except:
            raise HTTPError(400, "failed to parse ObjectId [%s]", _id)
