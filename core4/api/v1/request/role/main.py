import core4.queue.helper
import core4.util
from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.request.role.model import Role


class RoleHandler(CoreRequestHandler):
    title = "role and user management"
    author = "mra"
    protected = True

    async def post(self):
        pass
    #     ObjectIdField("_id", **kwargs),
    #     StringField("name", required=True, regex=ALPHANUM, **kwargs),
    #     StringField("realname", **kwargs),
    #     BoolField("is_active", **kwargs),
    #     TimestampField("created", **kwargs),
    #     TimestampField("updated", **kwargs),
    #     ObjectIdField("etag", **kwargs),
    #     RoleField("role", self.config.sys.role, **kwargs),
    #     StringField("email", required=False, regex=EMAIL, **kwargs),
    #     PasswordField("password", **kwargs),
    #     PermField("perm", **kwargs),
    #     TimestampField("last_login", **kwargs),
    #     QuotaField("quota", **kwargs),
    #
    #     pass
    #