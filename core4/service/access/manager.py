# -*- coding: utf-8 -*-


import core4.api.v1.role
import core4.base
import core4.service.access.handler.mongo

HANDLER = {
    "mongodb": core4.service.access.handler.mongo.MongoHandler
}


class CoreAccessManager(core4.base.CoreBase):

    def __init__(self, role, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if isinstance(role, str):
            role = core4.api.v1.role.Role().load_one(name=role)
        self.role = role

    def synchronise(self):
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
