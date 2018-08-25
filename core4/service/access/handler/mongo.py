# -*- coding: utf-8 -*-


import random
import string

from core4.service.access.handler import BaseHandler

#: password length used to create MongoDB access
PASSWORD_LENGTH = 32


class MongoHandler(BaseHandler):

    """
    This class handles MongoDB access permissions. The handler is registered
    in :attr:core4.service.access.manager.HANDLER` attribute.
    """
    def __init__(self, role, *args, **kwargs):
        super().__init__(role, *args, **kwargs)
        self.token = None
        self.admin_db = self.config.sys.admin.connection[
            self.config.sys.admin.database]

    def create_token(self):
        """
        This method creates a random password of length :attr:`PASSWORD_LENGTH`
        for the user to access the database

        :return: token/password (str)
        """
        if self.token is None:
            token = ''.join(
                random.SystemRandom().choice(
                    string.ascii_uppercase + string.digits) for _
                in range(PASSWORD_LENGTH))
            self.token = token
        return self.token

    def del_role(self):
        """
        This method deletes the MongoDB user and role if exist.
        """
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
        """
        This method creates the role and returns the token/password created by
        :meth:`.create_token`.

        .. note:: The user is created in MongoDB admin system database,
                  collection ``system.users``. Additionally a role is created
                  with the same name to grant read/write access permissions
                  to the custom user collection ``<USERNAME>`` in database
                  ``user``.

        :return: token/password (str)
        """
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
