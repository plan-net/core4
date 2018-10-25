from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.role.main import Role
from core4.error import Core4RoleNotFound


class ProfileHandler(CoreRequestHandler):

    """
    parameters
    ==========

    response
    ========

    example
    =======

    .. code-block:: json

        {
            "_id": "5bd01a80de8b693f4a68653c",
            "timestamp": "2018-10-24T07:08:48.744966",
            "code": 200,
            "message": "OK",
            "data": {
                "_id": "5bcdf7a7de8b690ae59d9557",
                "etag": "5bcdf7a7de8b690ae59d9556",
                "name": "admin",
                "realname": "default admin user",
                "email": "mail@mailer.com",
                "is_active": True,
                "created": "2018-10-22T16:15:35.659000",
                "last_login": "2018-10-24T07:08:43.758000",
                "role": ["admin"],
                "perm": ["cop"]
            }
        }
    """

    def get(self):
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
