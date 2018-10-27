import asyncio
import traceback
import datetime
import jwt
import mimeparse
import pandas as pd
import time
import tornado.escape
import tornado.httputil
from bson.objectid import ObjectId
from tornado.web import RequestHandler, HTTPError
import base64
import core4.util
from core4.api.v1.role.main import Role
from core4.api.v1.util import json_encode, json_decode
from core4.base.main import CoreBase

tornado.escape.json_encode = json_encode


class BaseHandler(CoreBase):
    protected = True
    title = None
    author = None

    async def prepare(self):
        """
        Prepares the handler with

        * setting the ``request_id``
        * preparing the combined parsing of query and body arguments
        * authenticate and authorize the user
        """
        self.identifier = ObjectId()
        if not (self.request.query_arguments or self.request.body_arguments):
            if self.request.body:
                body_arguments = json_decode(self.request.body.decode("UTF-8"))
                for k, v in body_arguments.items():
                    self.request.arguments.setdefault(k, []).append(v)
        if self.protected:
            user = await self.verify_user()
            if user:
                self.current_user = user.name
                if self.verify_access():
                    return
            self.redirect(self.get_login_url())
            # self.write_error(401)

    async def verify_user(self):
        """
        Extracts client's authorization from

        # Basic Authorization header, or from
        # Bearer Authorization header, or from
        # token parameter (query string or json body), or from
        # passed username and password parameters (query string or json body)

        :return:  verified username
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
            username = self.get_argument("username", None)
            password = self.get_argument("password", None)
            if token is not None:
                source = ("token", "args")
            elif username and password:
                source = ("username", "args")
            else:
                source = ("token", "cookie")
                token = self.get_secure_cookie("token")
        if token:
            payload = self._parse_token(token)
            username = payload.get("name")
            try:
                # user = await self.load_user(username)
                user = Role().load_one(name=username)
            except:
                self.logger.warning(
                    "failed to load [%s] by [%s] from [%s]", username, *source)
            else:
                self.token_exp = datetime.datetime.fromtimestamp(
                    payload["exp"])
                renew = self.config.api.token.refresh
                if (core4.util.now()
                        - datetime.datetime.fromtimestamp(
                            payload["timestamp"])).total_seconds() > renew:
                    self._create_token(username)
                    self.logger.debug("refresh token [%s] to [%s]", username,
                                      self.token_exp)
                self.logger.debug(
                    "successfully loaded [%s] by [%s] from [%s] expiring [%s]",
                    username, *source, self.token_exp)
                return user
        elif username and password:
            try:
                # user = await self.load_user(username)
                user = Role().load_one(name=username)
            except:
                self.logger.warning(
                    "failed to load [%s] by [%s] from [%s]", username, *source)
            else:
                if user.verify_password(password):
                    self.token_exp = None
                    return user
        return None

    def _create_token(self, username):
        secs = self.config.api.token.expiration
        payload = {
            'name': username,
            'timestamp': core4.util.now().timestamp()
        }
        token = self._create_jwt(secs, payload)
        self.set_secure_cookie("token", token)
        self.set_header("token", token)
        return token

    def _create_jwt(self, secs, payload):
        self.logger.debug("set token lifetime to [%d]", secs)
        expires = datetime.timedelta(
            seconds=secs)
        secret = self.config.api.token.secret
        algorithm = self.config.api.token.algorithm
        self.token_exp = (core4.util.now() + expires).replace(microsecond=0)
        payload["exp"] = self.token_exp
        token = jwt.encode(payload, secret, algorithm)
        return token.decode("utf-8")

    # def verify_token(self):
    #     """
    #     Authenticates the user with
    #
    #     # Basic Authorization header, or from
    #     # Bearer Authorization header, or from
    #     # token parameter (query string or json body), or from
    #     # passed username and password parameters (query string or json body)
    #
    #     :return:  verified username
    #     """
    #     auth_header = self.request.headers.get('Authorization')
    #     token = self.get_argument("token", default=None)
    #     if auth_header is not None:
    #         auth_type = auth_header.split()[0].lower()
    #         if auth_type == "bearer":
    #             token = auth_header[7:]
    #     elif token is None:
    #         token = self.get_secure_cookie("token")
    #         self.logger.info("encountered cookie [%s]", token)
    #     if token:
    #         payload = self._parse_token(token)
    #         self.token_exp = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(
    #             payload["exp"]
    #         ))
    #         return payload.get("name")
    #     return None

    def _parse_token(self, token):
        secret = self.config.api.token.secret
        algorithm = self.config.api.token.algorithm
        try:
            return jwt.decode(token, key=secret, algorithms=[algorithm],
                              verify=True)
        except jwt.ExpiredSignatureError:
            return {}

    def verify_access(self):
        raise NotImplementedError


class CoreRequestHandler(BaseHandler, RequestHandler):
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


    def verify_access(self):
        try:
            user = Role().load_one(name=self.current_user)
        except:
            self.logger.warning("username [%s] not found", self.current_user)
        else:
            if user.has_api_access(self.qual_name()):
                return True
        return False

    async def run_in_executor(self, meth, *args):
        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(
            self.application.container.executor, meth, *args)
        return await future

    def _wants(self, value, set_content=True):
        expect = self.guess_content_type() == value
        if expect and set_content:
            self.set_content_type(value)
        return expect

    def set_content_type(self, value):
        self.set_header("Content-Type", value + "; charset=UTF-8")

    def wants_json(self):
        return self._wants("application/json")

    def wants_html(self):
        return self._wants("text/html")

    def wants_text(self):
        return self._wants("text/plain")

    def wants_csv(self):
        return self._wants("text/csv")

    def guess_content_type(self):
        return mimeparse.best_match(
            self.supported_types, self.request.headers.get("accept", ""))

    def reply(self, chunk):
        """
        The method wraps Tornado's ``.write`` method featuring the following
        content types:

                    application/json    text/html   text/plain  text/csv
        DataFrame   .to_dict            .to_html    .to_string  .to_csv
        dict        .dumps              .dumps      .dumps      error
        str         put into .data      .render     .write      error

        * ``application/json``
        * ``text/html``
        * ``text/plain``
        * ``text/csv``

        :param chunk:
        :return:
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
        if isinstance(chunk, dict) or self.wants_json():
            chunk = self._build_json(
                message=self._reason,
                code=self.get_status(),
                data=chunk
            )
        self.finish(chunk)

    def _build_json(self, message, code, **kwargs):
        ret = {
            "_id": self.identifier,
            "timestamp": core4.util.now(),
            "message": message,
            "code": code
        }
        for extra in ("error", "data"):
            if extra in kwargs:
                ret[extra] = kwargs.get(extra)
        return ret

    def write_error(self, status_code, **kwargs):
        self.set_status(status_code)
        var = {
            "code": status_code,
            "message": tornado.httputil.responses[status_code],
            "contact": self.config.api.contact,
            "_id": self.identifier,
        }
        if self.settings.get("serve_traceback") and "exc_info" in kwargs:
            error = []
            for line in traceback.format_exception(*kwargs["exc_info"]):
                error.append(line)
            var["error"] = "\n".join(error)
        elif "exc_info" in kwargs:
            var["error"] = str(kwargs["exc_info"][1])
        if self.wants_json():
            self.finish(self._build_json(**var))
        elif self.wants_html():
            self.render(self.error_html_page, **var)
        elif self.wants_text() or self.wants_csv():
            self.render(self.error_text_page, **var)

    def abort(self, status_code, message=None):
        raise HTTPError(status_code, message or "unknown")

# todo: how to handle warnings, e.g. the signature has expired as an additional warning to 401 with error "Unauthorized"
# todo: request handler default properties management by configuration
