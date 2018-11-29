from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.request.role.model import CoreRole
from core4.error import Core4RoleNotFound
from bson.objectid import ObjectId
import core4.error
from tornado.web import HTTPError
import pymongo.errors

class ProfileHandler(CoreRequestHandler):
    title = "details for the logged in user"
    author = "mra"

    async def get(self):
        """
        User and role details for the current logged in user.

        Parameters:
            None

        Returns:
            data element with

            - **_id** (*str*): user _id
            - **_etag** (*str*): specifies the current version of the user
              profile
            - **name** (*str*)
            - **realname** (*str*)
            - **email** (*str*)
            - **is_active** (*bool*)
            - **role** (*list*): of role names assigned to the user
            - **perm** (*list*): of permissions collected from all assigned
              roles
            - **created** (*str*): in ISO format
            - **updated** (*str*): in ISO format
            - **last_login** (*str*): in ISO format
            - **token_expires** (*str*): in ISO format

        .. note:: The attribute ``token_expires`` is not extracted from
                  ``sys.user`` but from the user token exchanged between
                  client and server.

        Raises:
            401: Unauthorized

        Examples:
            >>> from requests import get, post
            >>> url = "http://localhost:5001/core4/api/v1"
            >>> signin = post(url + "/login", json={"username": "admin", "password": "hans"})
            >>> get(url + "/profile", cookies=signin.cookies).json()
            {
                '_id': '5bd9bbbbde8b69387b34c27a',
                'code': 200,
                'message': 'OK',
                'timestamp': '2018-10-31T14:27:07.153576',
                'data': {
                    '_id': '5bcdf7a7de8b690ae59d9557',
                    'created': '2018-10-22T16:15:35.659000',
                    'email': 'mail@mailer.com',
                    'etag': '5bd9a6b0de8b6925021dc2b9',
                    'is_active': True,
                    'last_login': '2018-10-31T14:27:00.731000',
                    'name': 'admin',
                    'perm': ['cop'],
                    'realname': 'default admin user',
                    'role': ['admin'],
                    'token_expires': '2018-10-31T16:27:00',
                    'updated': '2018-10-31T12:57:20.281000'
                }
            }
        """
        user = await CoreRole().find_one(name=self.current_user)
        if user is None:
            raise Core4RoleNotFound("unknown user [{}]".format(
                self.current_user
            ))
        doc = await user.detail()
        doc["token_expires"] = self.token_exp
        self.reply(doc)

    async def put(self):
        user = await CoreRole().find_one(name=self.current_user)
        if user is None:
            raise Core4RoleNotFound("unknown user [{}]".format(
                self.current_user
            ))
        kwargs = dict(
            etag=self.get_argument(
                "etag", as_type=ObjectId),
            realname=self.get_argument(
                "realname", as_type=str, default=None),
            email=self.get_argument(
                "email", as_type=str, default=None),
            password=self.get_argument(
                "password", as_type=str, default=None)
        )
        for k, v in kwargs.items():
            if v is not None:
                user.data[k].set(v)
        try:
            saved = await user.save()
        except (AttributeError, TypeError, core4.error.Core4ConflictError,
                core4.error.ArgumentParsingError) as exc:
            raise HTTPError(400, exc.args[0])
        except pymongo.errors.DuplicateKeyError:
            raise HTTPError(400, "name or email exists")
        except core4.error.Core4RoleNotFound as exc:
            raise HTTPError(400, "role [%s] not found", exc.args[0])
        except:
            raise
        else:
            if saved:
                self.reply(user.to_response())
            else:
                self.reply("no changes")
