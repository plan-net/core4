import base64

import datetime
import jwt

import core4.util
from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.role.main import Role


class LoginHandler(CoreRequestHandler):
    protected = False

    def get(self):
        self.post()

    def post(self):
        username = self.verify_user()
        if username:
            token = self._create_token(username)
            self.set_current_user(username)
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
