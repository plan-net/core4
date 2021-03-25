#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from tornado.web import HTTPError

import core4.queue.helper.functool
import core4.queue.helper.job
from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.request.role.model import CoreRole
from core4.api.v1.request.store import CoreStore


from core4.util.email import RoleEmail

class LoginHandler(CoreRequestHandler):
    """
    core4os standard Login Handler.
    """
    title = "Login Handler"
    author = "mra"
    protected = False

    async def get(self):
        """
        Same as :meth:`.post`
        """
        login = True
        if "reset" in self.request.path:
            login = False
        await self.getter(login)

    async def getter(self, login=True):
        if self.wants_html():
            store = await CoreStore.load(self.user)
            params = {
                "login_url": store["doc"]["login"],
                "reset_url": store["doc"]["reset"]
            }
            if login:
                return self.render("template/login.html", **params)
            return self.render("template/reset.html", **params)
        token = await self._login()
        if token:
            return self.reply({"token": token})
        self.set_status(401)
        self.write_error(401)


    async def post(self):
        """
        Login using *Basic Auth* header, *Bearer Auth* header, token parameter,
        token cookie or username/password parameter.

        Methods:
            POST /core4/api/v1/login

        Parameters:
            - username (str): requesting login
            - password (str): requesting login

        Returns:
            data element with

            - **token** (*str*): the created authorization token

        Raises:
            401: Unauthorized

        Examples:
            >>> from requests import get, post
            >>> url = "http://localhost:5001/core4/api/login"
            >>> rv = get(url + "?username=admin&password=hans")
            >>> rv.json()
            {
                '_id': '5bd94d9bde8b6939aa31ad88',
                'code': 200,
                'data': {
                    'token': 'eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9...'
                },
                'message': 'OK',
                'timestamp': '2018-10-31T06:37:15.734609'
            }
            >>> rv.headers
            {
                'Access-Control-Allow-Headers': 'access-control-allow-origin,authorization,content-type',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Origin': '*',
                'Content-Length': '339',
                'Content-Type': 'application/json; charset=UTF-8',
                'Date': 'Wed, 31 Oct 2018 06:37:15 GMT',
                'Etag': '"d62ecba1141f2653ebd4d9a54f677701e3f6337f"',
                'Server': 'TornadoServer/5.1.1',
                'Set-Cookie': 'token="2|1:0|10:1540967835|5:token|280:ZXlK..."; '
                'expires=Fri, 30 Nov 2018 06:37:15 GMT; Path=/',
                'Token': 'eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjo...'
            }
            >>> signin = post(url, json={"username": "admin", "password": "hans"})
            >>> post(url, cookies=signin.cookies)
            <Response [200]>
            >>> h = {"Authorization": "Bearer " + signin.json()["data"]["token"]}
            >>> post(url, headers=h)
            <Response [200]>
            >>> get("http://localhost:5001/core4/api/profile", headers=h)
            <Response [200]>
        """
        token = await self._login()
        if token:
            return self.reply({
                "token": token
            })
        self.set_status(401)
        self.write_error(401)
        # raise HTTPError(401)

    async def _login(self):
        user = await self.verify_user()
        if user:
            token = self.create_token(user.name)
            self.current_user = user.name
            # await user.login()
            return token
        return None

    async def put(self):
        """
        User password reset.

        ``PUT`` with an existing ``email`` parameter starts the password  reset
        workflow and sends a password reset token by email. ``PUT`` with this
        ``token`` and a new ``password`` updates the user's password and
        finishes the password reset workflow.

        The email with the reset password token is sent with a seperate job.
        Check core4 logging or ``sys.queue`` regarding the email and token
        (see :ref:`tools`)

        Methods:
            PUT /core4/api/v1/login

        Parameters:
            - email (str): of the user who requests to reset his password
            - token (str): of the authenticated user
            - password (str): the new password to set

        Returns:
            dict with empty data element

        Raises:
            400: Bad Request (if no email or token/password is sent)

        Examples:
            >>> from requests import get, put
            >>> url = "http://localhost:5001/core4/api/login"
            >>> put(url + "?email=mail@mailer.com").json()
            {
                '_id': '5bd9a525de8b691c2c0754d8',
                'code': 200,
                'data': None,
                'message': 'OK',
                'timestamp': '2018-10-31T12:50:45.919375'
            }
            >>> # check logging for reset token if email not sent
            >>> token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJuYW..."
            >>> put(url + "?password=hans&token=" + token).json()
            {
                '_id': '5bd9a619de8b691c2ca2d0d0',
                'code': 200,
                'data': 'OK',
                'message': 'OK',
                'timestamp': '2018-10-31T12:54:50.106412'
            }
        """
        email = self.get_argument("email", default=None)
        token = self.get_argument("token", default=None)
        password = self.get_argument("password", default=None)
        if email:
            await self._start_password_reset(email)
        elif token and password:
            await self._finish_password_reset(token, password)
        else:
            raise HTTPError(400)

    async def _start_password_reset(self, email):
        # internal method to create and send the password reset token
        self.logger.debug("enter password reset for [%s]", email)
        user = await CoreRole().find_one(email=email)
        if user is None:
            self.logger.warning("email [%s] not found", email)
        else:
            username = user.name
            self.current_user = username
            secs = self.config.api.reset_password.expiration
            payload = {
                'email': email,
                'name': username,
            }
            token = self.create_jwt(secs, payload)
            # self._send_mail(email, user.realname, token)
            core4.queue.helper.functool.enqueue(
                RoleEmail,
                template=self.config.email.template.en.password_reset,
                recipients=email,
                subject="core4: your password reset request",
                realname=user.realname,
                token=token,
                username=user.name
            )
            self.logger.info("send token [%s] to user [%s] at [%s]",
                             token, username, email)
        self.reply(None)

    async def _finish_password_reset(self, token, password):
        # internal method to set the updated password
        payload = self.parse_token(token)
        try:
            user = await CoreRole().find_one(name=payload["name"])
        except:
            self.logger.warning("user [%s] not found", payload["name"])
        user.password = password
        await user.save()
        self.logger.debug(
            "finish password reset for user [%s]", payload["name"])
        self.reply("OK")
