from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.role.main import Role
from core4.error import Core4RoleNotFound


class ProfileHandler(CoreRequestHandler):
    title = "details for the logged in user"
    author = "mra"

    def get(self):
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
        try:
            user = Role().load_one(name=self.current_user)
        except:
            raise Core4RoleNotFound("unknown user [{}]".format(
                self.current_user
            ))
        else:
            doc = user.detail()
            doc["token_expires"] = self.token_exp
            self.reply(doc)
