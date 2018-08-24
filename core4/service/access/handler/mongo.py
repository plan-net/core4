# -*- coding: utf-8 -*-


import core4.base
import random
import string


PASSWORD_LENGTH = 32


class MongoHandler(core4.base.CoreBase):

    def __init__(self, role, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.role = role
        self.token = None
        self.admin_db = self.config.sys.admin.connection[
            self.config.sys.admin.database]

    def create_token(self):
        if self.token is None:
            token = ''.join(
                random.SystemRandom().choice(
                    string.ascii_uppercase + string.digits) for _
                in range(PASSWORD_LENGTH))
            self.token = token
        return self.token

    def del_role(self):
        # delete the role
        username = self.role.name
        user_info = self.admin_db.command("usersInfo", username)
        if user_info["users"]:
            self.admin_db.command('dropUser', username)
            self.logger.info('removed mongo user [%s]', username)
        else:
            self.logger.debug("mongo user [%s] not found", username)
        role_info = self.admin_db.command("rolesInfo", username)
        if role_info["roles"]:
            self.admin_db.command('dropRole', username)
            self.logger.info('removed mongo role [%s]', username)
        else:
            self.logger.debug("mongo user [%s] not found", username)

    def add_role(self):
        # create the role
        username = self.role.name
        password = self.create_token()
        privileges = [
            {
                "resource": {
                    "db": "user",
                    "collection": username
                },
                "actions": [
                    "find", "insert", "remove", "update"
                ]
            }
        ]
        self.admin_db.command('createRole', username, roles=[],
                              privileges=privileges)
        self.logger.info('created mongo role [%s]', username)
        self.admin_db.command('createUser', username, pwd=password,
                              roles=[username])
        self.logger.info('created mongo user [%s]', username)

        return password

    def grant(self, database):
        # cascade db permission, then grant read-only access
        username = self.role.name
        self.admin_db.command('grantRolesToUser', username,
                              roles=[{'role': 'read', 'db': database}])
        self.logger.info('grant role [%s] access to [%s]', username, database)

    def finish(self):
        pass
