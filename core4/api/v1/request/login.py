import base64

import datetime
import jwt
import core4.util
import core4.queue.helper
from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.role.main import Role


class LoginHandler(CoreRequestHandler):
    """
    Login and password reset resource.

    url
    ===

    * GET/POST /core4/api/v1/login?username&password - login
    * PUT /core4/api/v1/login?email - request password reset token
    * PUT /core4/api/v1/login?token&password - reset password

    parameters
    ==========

    * username
    * password

    response
    ========

    * 200 OK
    * 401 Unauthorized

    example
    =======

    .. code-block:: json

        {
        }

    """
    protected = False

    async def get(self):
        await self.post()

    async def post(self):
        username = await self.verify_user()
        if username:
            token = self._create_token(username)
            self.current_user = username
            return self.reply({
                "token": token
            })
        self.set_header('WWW-Authenticate', 'Basic realm=Restricted')
        self.set_status(401)
        if self.wants_json():
            self.write_error(401)

    def _create_token(self, username):
        secs = self.config.api.token.expiration
        payload = {
            'name': username,
        }
        return self._create_jwt(secs, payload)

    def _create_jwt(self, secs, payload):
        self.logger.debug("set token lifetime to [%d]", secs)
        expires = datetime.timedelta(
            seconds=secs)
        secret = self.config.api.token.secret
        algorithm = self.config.api.token.algorithm
        payload["exp"] = core4.util.now() + expires
        token = jwt.encode(payload, secret, algorithm)
        return token.decode("utf-8")

    async def verify_user(self):
        auth_header = self.request.headers.get('Authorization')
        username = password = None
        token = None
        if auth_header is not None:
            auth_type = auth_header.split()[0].lower()
            if auth_type == "basic":
                auth_decoded = base64.decodebytes(
                    auth_header[6:].encode("utf-8"))
                username, password = auth_decoded.decode(
                    "utf-8").split(':', 2)
            elif auth_type == "bearer":
                token = auth_header[7:]
        else:
            token = self.get_argument("token", default=None)
            username = self.get_argument("username", None)
            password = self.get_argument("password", None)
        if token:
            payload = self._parse_token(token)
            return payload.get("name")
        if username and password:
            try:
                #user = await self.load_user(username)
                user = Role().load_one(name=username)
            except:
                self.logger.warning("username [%s] not found", username)
            else:
                if user.verify_password(password):
                    user.login()
                    return username
        return None

    def put(self):
        email = self.get_argument("email", None)
        token = self.get_argument("token", None)
        password = self.get_argument("password", None)
        if email:
            self.start_password_reset(email)
        elif token and password:
            self.finish_password_reset(token, password)
        else:
            self.abort(400)

    def start_password_reset(self, email):
        self.logger.debug("enter password reset for [%s]", email)
        try:
            user = Role().load_one(email=email)
        except:
            self.logger.warning("email [%s] not found", email)
        else:
            username = user.name
            secs = self.config.api.reset_password.expiration
            payload = {
                'email': email,
                'name': username,
            }
            token = self._create_jwt(secs, payload)
            self.send_mail(email, user.realname, token)
            self.logger.info("send token [%s] to user [%s] at [%s]",
                             token, username, email)
        self.reply(None)

    def finish_password_reset(self, token, password):
        payload = self._parse_token(token)
        try:
            user = Role().load_one(name=payload["name"])
        except:
            self.logger.warning("user [%s] not found", payload["name"])
        user.password = password
        user.save()
        self.logger.debug("finish password reset for user [%s] with [%s]",
                          payload["name"], password)
        self.reply("OK")

    def send_mail(self, email, realname, token):
        core4.queue.helper.enqueue(
            core4.queue.helper.MailerJob,
            template="",
            recipients=email,
            subject="core4: your password reset request",
            realname=realname,
            token=token
        )

    # async def load_user(self, username):
    #     doc = await self.motor.core4test.sys.role.find_one({'name': username})
    #     doc["password_hash"] = doc["password"]
    #     del doc["password"]
    #     return Role(**doc)