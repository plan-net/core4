import base64

import datetime
import jwt
import core4.util
import core4.queue.helper
from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.role.main import Role


class LogoutHandler(CoreRequestHandler):

    protected = False

    async def get(self):
        await self.post()

    async def post(self):
        self.current_user = None
        self.set_secure_cookie("token", "")
        self.reply("OK")