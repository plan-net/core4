#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from core4.api.v1.request.role.access.handler import BaseHandler
import momoko

PREP_DATABASE = """
REVOKE ALL ON SCHEMA public FROM public;
REVOKE ALL ON DATABASE {dbname:s} FROM public;

REVOKE CREATE ON SCHEMA public FROM {dbrole:s};
REVOKE ALL ON DATABASE {dbname:s} FROM {dbrole:s};

GRANT CONNECT ON DATABASE {dbname:s} TO {dbrole:s};
GRANT CONNECT ON DATABASE {dbname:s} TO {superuser:s};

GRANT SELECT ON ALL TABLES IN SCHEMA public TO {dbrole:s};
GRANT USAGE ON SCHEMA public TO {dbrole:s};

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO {dbrole:s};
"""

DROP_DATABASE = """
UPDATE pg_database SET datallowconn = 'false' WHERE datname = '{dbname:s}';
ALTER DATABASE {dbname:s} CONNECTION LIMIT 1;
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{dbname:s}';
"""


class PostgresHandler(BaseHandler):
    """
    """

    def __init__(self, role=None, token=None, *args, **kwargs):
        super().__init__(role, token, *args, **kwargs)
        self.dsn = 'dbname=%s user=%s password=%s host=%s port=%d' %(
            self.config.rdbms.database,
            self.config.rdbms.username,
            self.config.rdbms.password,
            self.config.rdbms.hostname,
            self.config.rdbms.port
        )
        self._connection = None

    @property
    async def connection(self):
        if self._connection is None:
            #self.logger.info("connecting to [%s]", self.dsn)
            conn = momoko.Connection(dsn=self.dsn)
            self._connection = await conn.connect()
        return self._connection

    async def role_exists(self,  name):
        sql = "SELECT 1 FROM pg_roles WHERE rolname='%s'" % name
        cursor = await self.connection
        rows = await cursor.execute(sql)
        return rows.fetchall() != []

    async def database_exists(self,  name):
        sql = "SELECT 1 FROM pg_database WHERE datname='%s'" % name
        cursor = await self.connection
        rows = await cursor.execute(sql)
        return rows.fetchall() != []

    async def del_role(self):
        """
        This method deletes the Postgresql user and role if exist.
        """
        if await self.role_exists(self.role.name):
            cursor = await self.connection
            await cursor.execute('DROP ROLE "%s"' % self.role.name)
            self.logger.info('removed postgres role [%s]', self.role.name)
        else:
            self.logger.debug("postgres role [%s] not found", self.role.name)

    async def add_role(self):
        """
        This method creates the role and returns the token/password created by
        :meth:`.create_token`.

        .. note:: The user is created in MongoDB admin system database,
                  collection ``system.users``. Additionally the MongoDB
                  built-in role *dbOwner* is granted on database
                  ``user!<USERNAME>``. The prefix *user!* can be configured
                  with core4 configuration option ``sys.userdb``.

        :return: token/password (str)
        """
        # create the role
        cursor = await self.connection
        await cursor.execute("CREATE ROLE \"%s\" WITH LOGIN PASSWORD '%s'" % (
            self.role.name, self.token))
        self.logger.info(
            'created postgres role [%s]', self.role.name)
        return self.token

    async def create_database(self, name):
        cursor = await self.connection
        await cursor.execute('CREATE DATABASE "%s"' % name)
        self.logger.info(
            'created postgres database [%s]', name)
        db_role = "ro_" + name
        cursor = await self.connection
        await cursor.execute('CREATE ROLE "%s"' % db_role)
        self.logger.info(
            'created postgres role [%s]', db_role)
        dsn = 'dbname=%s user=%s password=%s host=%s port=%d' %(
            name,
            self.config.rdbms.username,
            self.config.rdbms.password,
            self.config.rdbms.hostname,
            self.config.rdbms.port
        )
        conn = momoko.Connection(dsn=dsn)
        cursor = await conn.connect()
        sql = PREP_DATABASE.format(
            dbname=name, dbrole=db_role, superuser=self.config.rdbms.username
        )
        return await cursor.execute(sql)


    async def del_database(self, name):
        db_role = "ro_" + name
        cursor = await self.connection
        sql = DROP_DATABASE.format(dbname=name, dbrole=db_role)
        await cursor.execute(sql)
        cursor = await self.connection
        await cursor.execute("DROP DATABASE %s" % name)
        self.logger.info('dropped postgres database [%s]', name)
        cursor = await self.connection
        await cursor.execute("DROP ROLE %s" % db_role)
        self.logger.info('dropped postgres role [%s]', db_role)

    async def grant(self, database):
        """
        cascade database permissions and read-only access.

        :param database: to grant
        """
        if not await self.database_exists(database):
            await self.create_database(database)
        db_role = "ro_" + database
        cursor = await self.connection
        await cursor.execute('GRANT "%s" TO "%s"' % (db_role,
                                                  self.role.name))
        self.logger.info(
            'grant postgres database [%s] to [%s]', database, self.role.name)
