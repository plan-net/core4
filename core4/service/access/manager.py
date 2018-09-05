# -*- coding: utf-8 -*-


import core4.api.v1.role
import core4.base
import core4.error
import core4.service.access.handler.mongo

#: key/value pairs of permission protocols and access handlers
HANDLER = {
    "mongodb": core4.service.access.handler.mongo.MongoHandler
}


class CoreAccessManager(core4.base.CoreBase):
    """
    The :class:`.CoreAccessManager` processes all permissions defined for a
    core4 role. The :meth:`synchronise` method executes the following workflow
    for all protocols with the appropriate access handler as defined in module
    variable :attr:`HANDLER`:

    #. delete role if it exists (handler method ``.del_role()``)
    #. create the role (handler method ``.add_role()``)
    #. create access token (password to be used together with the role`s  name)
    #. grant read permissions for each permission with the appropriate protocol
       (handler method ``.grant(db)``)
    #. call the handler's ``.finish()`` method

    Currently only the handler :class:`.MongoHandler` is defined to grant
    read-only permissions to MongoDB databases (e.g. ``mongodb://dbname``) and
    read/write access permissions to the role's custom collection in MongoDB
    database `user` (e.g. MongoDB collection ``user.<USERNAME>``).
    """

    def __init__(self, role, *args, **kwargs):
        """
        Initialises access management for the passed core4 role/user.

        :param role: :class:`.core4.api.v1.role.Role` or role name (str)
        """
        super().__init__(*args, **kwargs)
        if isinstance(role, str):
            role = core4.api.v1.role.Role().load_one(name=role)
        if not role.is_user:
            raise core4.error.Core4UsageError(
                "cannot synchronise core4 roles, only users")
        self.role = role

    def synchronise(self):
        """
        Executes the access management workflow for each handler as defined
        by the role's access permission (see :class:`.PermField` and
        :class:`.Role`.

        :return: dict of protocol and access token (password)
        """
        access = {}
        for proto in HANDLER:
            handler = HANDLER[proto](self.role)
            handler.del_role()
            access[proto] = handler.add_role()
        service = {}
        for perm in self.role._casc_perm:
            (proto, *database) = perm.split("://")
            if proto in HANDLER:
                if proto not in service:
                    service[proto] = []
                service[proto].append("://".join(database))
        for proto, db_list in service.items():
            for db in db_list:
                handler.grant(db)
            handler.finish()
        return access
