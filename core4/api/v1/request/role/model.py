import re
from core4.base import CoreBase
from core4.api.v1.role.field import *

ALPHANUM = re.compile(r'^[a-zA-Z0-9_.-]+$')
EMAIL = re.compile(r'^[_a-z0-9-]+(\.[_a-z0-9-]+)*'
                   r'@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$')


class Role(CoreBase):
    """
    Access to core API, core4 jobs, databases and applications is managed
    through roles. Role data resides in core4 system collection ``sys.role``.

    Each role has the following attributes:

    * ``._id`` (:class:`.ObjectId`) mongo database identifier
    * ``.name`` (str)
    * ``.realname`` (str)
    * ``.is_active`` (bool)
    * ``.created`` (:class:`.datetime`), automatically injected
    * ``.updated`` (:class:`.datetime`), automatically injected
    * ``.etag`` (:class:`.ObjectId`) for concurrency control
    * ``.role`` (list of :class:`.Role`)
    * ``.email`` (str)
    * ``.password`` (str)
    * ``.perm`` (list of str)
    * ``.last_login`` (:class:`.datetime`), automatically injected
    * ``.quota`` (str in format ``limit:seconds``)

    Then ``name`` must be unique. The ``email`` must be unique for users (not
    roles) if defined.
    """

    def __init__(self, **kwargs):
        super().__init__()

        fields = [
            ObjectIdField("_id", **kwargs),
            StringField("name", required=True, regex=ALPHANUM, **kwargs),
            StringField("realname", **kwargs),
            BoolField("is_active", **kwargs),
            TimestampField("created", **kwargs),
            TimestampField("updated", **kwargs),
            ObjectIdField("etag", **kwargs),
            RoleField("role", self.config.sys.role, **kwargs),
            StringField("email", required=False, regex=EMAIL, **kwargs),
            PasswordField("password", **kwargs),
            PermField("perm", **kwargs),
            TimestampField("last_login", **kwargs),
            QuotaField("quota", **kwargs),
        ]

        self.data = dict([(f.key, f) for f in fields])
        for field in kwargs:
            if ((field not in self.data) and (field != "password_hash")):
                raise TypeError("unknown field [{}]".format(field))
        self.is_authenticated = False
        self.is_anonymous = False
        self._perm = None

