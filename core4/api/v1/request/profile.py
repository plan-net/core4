from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.role.main import Role
from core4.error import Core4RoleNotFound

class ProfileHandler(CoreRequestHandler):

    def get(self):
        try:
            # user = await self.load_user(username)
            user = Role().load_one(name=self.current_user)
        except:
            raise Core4RoleNotFound("unknown user [{}]".format(
                self.current_user
            ))
        else:
            self.reply(user.detail())
