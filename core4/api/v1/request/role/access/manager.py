from core4.api.v1.request.role.model import CoreRole
import core4.base
import core4.error
import core4.api.v1.request.role.access.handler.mongo
from tornado.ioloop import IOLoop

#: key/value pairs of permission protocols and access handlers
HANDLER = {
    "mongodb": core4.api.v1.request.role.access.handler.mongo.MongoHandler
}


class CoreAccessManager(core4.base.CoreBase):
    """
    The :class:`.CoreAccessManager` processes all permissions defined for a
    core4 role. The :meth:`synchronise` method executes the following workflow
    for all protocols with the appropriate access handler as defined in module
    variable :attr:`HANDLER`:

    #. delete role if it exists (handler method ``.del_role()``)
    #. create the role (handler method ``.add_role()``)
    #. create access token (password to be used together with the role`s name)
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

        :param role: :class:`.core4.api.v1.role.Role`
        """
        super().__init__(*args, **kwargs)
        if not role.is_user:
            raise core4.error.Core4UsageError(
                "cannot synchronise core4 roles, only users")
        self.role = role

    async def synchronise(self, protocol):
        """
        Executes the access management workflow for the passed handler as
        defined by the role's access permission (see :class:`.PermField` and
        :class:`.Role`.

        :return: access token (password)
        """
        handler = HANDLER[protocol](self.role)
        await handler.del_role()
        token = await handler.add_role()
        perms = await self.role.casc_perm()
        for perm in perms:
            (proto, *database) = perm.split("://")
            if proto == protocol:
                dbname = "://".join(database)
                await handler.grant(dbname)
        await handler.finish()
        return token

    async def synchronise_all(self):
        access = {}
        for proto in HANDLER:
            access[proto] = await self.synchronise(proto)
        return access

    async def reset(self, protocol):
        handler = HANDLER[protocol](self.role)
        await handler.del_role()

    async def reset_all(self):
        for proto in HANDLER:
            await self.reset(proto)