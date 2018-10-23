import base64

import datetime
import jwt
import motor
import core4.util
from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.role.main import Role


class LoginHandler(CoreRequestHandler):
    protected = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.motor = motor.MotorClient("mongodb://core:654321@localhost:27017")

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
        expires = datetime.timedelta(
            seconds=self.config.api.token.expiration)
        secret = self.config.api.token.secret
        algorithm = self.config.api.token.algorithm
        payload = {
            'name': username,
            'exp': core4.util.now() + expires
        }
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
                user = await self.load_user(username)
                #user = Role().load_one(name=username)
            except:
                self.logger.warning("username [%s] not found", username)
            else:
                if user.verify_password(password):
                    #user.login()
                    return username
        return None

    async def load_user(self, username):
        doc = await self.motor.core4test.sys.role.find_one({'name': username})
        doc["password_hash"] = doc["password"]
        del doc["password"]
        return Role(**doc)