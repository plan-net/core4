import core4.queue.helper
import core4.util
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
        user = await self.verify_user()
        if user:
            token = self._create_token(user.name)
            self.current_user = user.name
            user.login()
            return self.reply({
                "token": token
            })
        self.set_header('WWW-Authenticate', 'Basic realm=Restricted')
        self.set_status(401)
        if self.wants_json():
            self.write_error(401)

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
