from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.role.main import Role
from core4.error import Core4RoleNotFound

class ProfileHandler(CoreRequestHandler):

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
