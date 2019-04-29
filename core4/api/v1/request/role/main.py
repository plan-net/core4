#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import pymongo.errors
from bson.objectid import ObjectId
from tornado.web import HTTPError

import core4.error
from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.request.role.model import CoreRole
from core4.api.v1.request.role.access.manager import CoreAccessManager


class RoleHandler(CoreRequestHandler):
    title = "role and user management"
    author = "mra"
    tag = ["role management"]

    async def post(self, _id=None):
        """
        Creates a new user or role. Note that users are different to roles in
        that actual users have a valid :class:`.StringField` ``email`` and
        :class:`.PasswordField` ``password``. For roles both attributes must be
        ``None``.

        Methods:
            POST /roles - user/role creation

        Parameters:
            name (str): unique name of the user or role.
            realname (str): of the user or role
            is_active (bool): disable login and permission cascade with
                              ``True``
            role (list): of role names assigned
            email (str): for actual users; for roles the email attribute is
                         expected to be undefined or ``None``
            password (str): for actual users; for roles the password attribute
                            is expected to be undefined or ``None``
            perm (list): of permission protocols

        The following permission protocols exist:

        * ``cop`` - administrative role
        * ``job://[qual_name]/[xr]`` - job read and execution permission
        * ``api://[qual_name]`` - api access permission
        * ``app://[key]`` - app key permission
        * ``mongodb://[database]`` - MongoDB database access permission
          (read-only)

        Returns:
            data element with

            - **name** (*str*): of the user or role
            - **realname** (*str*): of the user or role
            - **is_active** (*bool*): indicating if the user/role is active
            - **role** (*list*): of cascading role names
            - **email** (*list*): of the user (not role)
            - **perm** (*list*): of cascading permission protocols

        Raises:
            400 Bad Request: AttributeError
            400 Bad Request: TypeError
            400 Bad Request: Core4ConflictError
            400 Bad Request: name or email exists
            401 Unauthorized:
            404 Bad Request: Core4RoleNotFound

        Examples:
            >>> from requests import get, post, delete, put
            >>> from pprint import pprint
            >>> import random
            >>> url = "http://localhost:5001/core4/api/v1"
            >>> signin = get(url + "/login?username=admin&password=hans")
            >>> token = signin.json()["data"]["token"]
            >>> h = {"Authorization": "Bearer " + token}
            >>>
            >>> rv = post(url + "/roles", headers=h,
            >>>           json={
            >>>               "name": "reporting",
            >>>               "realname": "Reporting User",
            >>>               "perm": ["api://reporting.api.v1.public"]
            >>>           })
            >>> rv.json()
            {
                '_id': '5bed0a9ade8b693044cb766e',
                'code': 200,
                'data': {
                    '_id': '5bed0a9ade8b693044cb7674',
                    'created': '2018-11-15T05:56:42',
                    'etag': '5bed0a9ade8b693044cb7672',
                    'is_active': True,
                    'name': 'reporting',
                    'perm': ['api://reporting.api.v1.public'],
                    'realname': 'Reporting User',
                    'role': []
                },
                'message': 'OK',
                'timestamp': '2018-11-15T05:56:42.562178'
            }
            >>> rv = post(url + "/roles", headers=h,
            >>>           json={
            >>>               "name": "test",
            >>>               "realname": "Test User",
            >>>               "role": ["reporting"],
            >>>               "email": "test@plan-net.com",
            >>>               "password": "tset resu",
            >>>               "perm": ["app://reporting/test"]
            >>>           })
            >>> rv
            <Response [200]>
        """
        kwargs = dict(
            name=self.get_argument(
                "name", as_type=str),
            realname=self.get_argument(
                "realname", as_type=str, default=""),
            is_active=self.get_argument(
                "is_active", as_type=bool, default=True),
            role=self.get_argument(
                "role", as_type=list, default=[]),
            email=self.get_argument(
                "email", as_type=str, default=None),
            password=self.get_argument(
                "password", as_type=str, default=None),
            perm=self.get_argument(
                "perm", as_type=list, default=[])
        )
        try:
            role = CoreRole(**kwargs)
            await role.save()
        except (AttributeError, TypeError, core4.error.Core4ConflictError,
                core4.error.ArgumentParsingError) as exc:
            raise HTTPError(400, exc.args[0])
        except pymongo.errors.DuplicateKeyError:
            raise HTTPError(400, "name or email exists")
        except core4.error.Core4RoleNotFound as exc:
            raise HTTPError(404, "role [%s] not found", exc.args[0])
        except:
            raise
        else:
            self.reply(role.to_response())

    async def get(self, _id=None):
        """
        Get users/roles listing and details.

        Methods:
            GET /roles - user/role listing

        Arguments:
            per_page (int): number of jobs per page
            page (int): requested page (starts counting with ``0``)
            sort (str): sort field
            order (int): sort direction (``1`` for ascending, ``-1`` for
                descending)


        Returns:
            data element with list of job attributes as dictionaries. See below
            for the list of attributes. For pagination the following top level
            attributes are returned:

            - **total_count** (int): the total number of records
            - **count** (int): the number of records in current page
            - **page** (int): current page (starts counting with ``0``)
            - **page_count** (int): the total number of pages
            - **per_page** (int): the number of elements per page

        Raises:
            400 Bad Request: AttributeError
            400 Bad Request: TypeError
            400 Bad Request: Core4ConflictError
            401 Unauthorized: Login required
            404 Bad Request: Core4RoleNotFound

        Examples:
            >>> rv = get(url + "/roles", headers=h)
            >>> rv.json()
                        '_id': '',
                        'created': '2018-11-15T05:56:42',
                        'etag': '5bed0a9ade8b693044cb7672',
                        'is_active': True,
                        'name': 'reporting',
                        'perm': ['api://reporting.api.v1.public'],
                        'realname': 'Reporting User',
                        'role': []
                    },
                    {
                        '_id': '5bed0b58de8b6930449e5b10',
                        'created': '2018-11-15T05:59:52',
                        'email': 'test@plan-net.com',
                        'etag': '5bed0b58de8b6930449e5b0e',
                        'is_active': True,
                        'name': 'test',
                        'perm': ['app://reporting/test'],
                        'realname': 'Test User',
                        'role': ['5bed0a9ade8b693044cb7674']
                    }],
                'message': 'OK',
                'page': 0,
                'page_count': 1,
                'per_page': 10,
                'timestamp': '2018-11-15T06:09:30.469962',
                'total_count': 3.0
            }

        Methods:
            GET /roles/<_id> - user/role detail

        Parameters:
            _id (str): of the user/role

        Returns:
            data element with

            - **name** (*str*): of the user or role
            - **realname** (*str*): of the user or role
            - **is_active** (*bool*): indicating if the user/role is active
            - **role** (*list*): of cascading role names
            - **email** (*list*): of the user (not role)
            - **perm** (*list*): of cascading permission protocols

        Raises:
            400 Bad Request: AttributeError
            400 Bad Request: TypeError
            400 Bad Request: Core4ConflictError
            401 Unauthorized:
            404 Bad Request: Core4RoleNotFound

        Examples:
            >>> rv = get(url + "/roles/5bed0a9ade8b693044cb7674", headers=h)
            >>> rv.json()
            {
                '_id': '5bed102fde8b697371789803',
                'code': 200,
                'data': {
                    '_id': '5bed0a9ade8b693044cb7674',
                    'created': '2018-11-15T05:56:42',
                    'etag': '5bed0a9ade8b693044cb7672',
                    'is_active': True,
                    'name': 'reporting',
                    'perm': ['api://reporting.api.v1.public'],
                    'realname': 'Reporting User',
                    'role': []
                },
                'message': 'OK',
                'timestamp': '2018-11-15T06:20:31.763471'
            }
        """
        if _id is None or _id.strip() == "":
            ret = await CoreRole().load(
                per_page=self.get_argument(
                    "per_page", as_type=int, default=10),
                current_page=self.get_argument(
                    "page", as_type=int, default=0),
                query_filter=self.get_argument(
                    "filter", as_type=dict, default={}),
                sort_by=self.get_argument(
                    "sort", as_type=str, default="_id"),
                sort_order=self.get_argument(
                    "order", as_type=int, default=1),
            )
            for doc in ret.body:
                doc.pop("password", None)
            self.reply(ret)
        else:
            oid = self.parse_objectid(_id)
            ret = await CoreRole().find_one(_id=oid)
            if ret is None:
                raise HTTPError(404, "role [%s] not found", oid)
            self.reply(await ret.detail())

    async def put(self, _id):
        """
        Update user/role attributes.

        Methods:
            PUT /roles/<_id> - user/role update

        Parameters:
            _id (str): of the user/role to update
            etag (str): of the user/role
            name (str): unique name of the user or role.
            realname (str): of the user or role
            is_active (bool): disable login and permission cascade with
                ``True``
            role (list): of role names assigned
            email (str): for actual users; for roles the email attribute is
                expected to be undefined or ``None``
            password (str): for actual users; for roles the password attribute
                is expected to be undefined or ``None``
            perm (list): of permission protocols. For valid permission
                protocols see ``POST`` method.

        Returns:
            If the requested update did not change any attribute, then
            ``no changes`` is returned in the data element. If changes have
            been applied successfully, then the data element contains the
            updated user/role attributes.

            - **name** (*str*): of the user or role
            - **realname** (*str*): of the user or role
            - **is_active** (*bool*): indicating if the user/role is active
            - **role** (*list*): of cascading role names
            - **email** (*list*): of the user (not role)
            - **perm** (*list*): of cascading permission protocols

        Raises:
            400 Bad Request: AttributeError
            400 Bad Request: TypeError
            400 Bad Request: Core4ConflictError
            401 Unauthorized:
            404 Bad Request: Core4RoleNotFound

        Examples:
            >>> rv = put(url + "/roles/5bed1271de8b6973711e9715",
            >>>          json={
            >>>              "email": "mail@mailer.com",
            >>>              "etag": "5bed1271de8b6973711e9713"}, headers=h)
            >>> rv
            <Response [400]>
            >>> rv.json()
            {
                '_id': '5bed2012de8b6973715571a8',
                'code': 400,
                'error': 'tornado.web.HTTPError: HTTP 400: Bad Request (name or email exists)...',
                'message': 'Bad Request',
                'timestamp': '2018-11-15T07:28:18.724144'
            }
            >>> rv = put(url + "/roles/5bed1271de8b6973711e9715",
            >>>          json={
            >>>              "email": "test@mailer.com",
            >>>              "etag": "5bed1271de8b6973711e9713"}, headers=h)
            >>> rv
            <Response [200]>
            {
                '_id': '5bed2026de8b6973715571b8',
                'code': 200,
                'data': {
                    '_id': '5bed1271de8b6973711e9715',
                    'created': '2018-11-15T06:30:09',
                    'email': 'test@mailer.com',
                    'etag': '5bed2027de8b6973715571c4',
                    'is_active': True,
                    'name': 'test',
                    'perm': ['app://reporting/test'],
                    'realname': 'Test User',
                    'role': ['reporting'],
                    'updated': '2018-11-15T07:28:39'
                },
                'message': 'OK',
                'timestamp': '2018-11-15T07:28:39.129893'
            }
        """
        oid = self.parse_objectid(_id)
        ret = await CoreRole().find_one(_id=oid)
        if ret is None:
            raise HTTPError(404, "role [%s] not found", oid)
        kwargs = dict(
            etag=self.get_argument(
                "etag", as_type=ObjectId),
            name=self.get_argument(
                "name", as_type=str, default=None),
            realname=self.get_argument(
                "realname", as_type=str, default=None),
            is_active=self.get_argument(
                "is_active", as_type=bool, default=None),
            role=self.get_argument(
                "role", as_type=list, default=None),
            email=self.get_argument(
                "email", as_type=str, default=None),
            password=self.get_argument(
                "password", as_type=str, default=None),
            perm=self.get_argument(
                "perm", as_type=list, default=None)
        )
        for k, v in kwargs.items():
            if v is not None:
                ret.data[k].set(v)
        try:
            saved = await ret.save()
        except (AttributeError, TypeError, core4.error.Core4ConflictError,
                core4.error.ArgumentParsingError) as exc:
            raise HTTPError(400, exc.args[0])
        except pymongo.errors.DuplicateKeyError:
            raise HTTPError(400, "name or email exists")
        except core4.error.Core4RoleNotFound as exc:
            raise HTTPError(404, "role [%s] not found", exc.args[0])
        except:
            raise
        else:
            if saved:
                self.reply(ret.to_response())
            else:
                self.reply("no changes")
        if "perm" in kwargs:
            self.logger.debug("revoke access grants")
            manager = CoreAccessManager(ret)
            await manager.reset_all()

    async def delete(self, _id):
        """
        Deletes an existing user or role.

        Methods:
            DELETE /roles/<_id>?etag=<etag>
            DELETE /roles/<_id>/<etag>

        Parameters:
            _id (str): of the user/role to delete
            etag (str): of the user/role

        Returns:
            data with ``True`` for success, else ``False``

            - **name** (*str*): of the user or role
            - **realname** (*str*): of the user or role
            - **is_active** (*bool*): indicating if the user/role is active
            - **role** (*list*): of cascading role names
            - **email** (*list*): of the user (not role)
            - **password** (*list*): of the user (not role)
            - **perm** (*list*): of cascading permission protocols

        Raises:
            400 Bad Request: AttributeError
            400 Bad Request: TypeError
            400 Bad Request: Core4ConflictError
            404 Bad Request: Core4RoleNotFound

        Examples:
            >>> rv = get(url + "/roles/5bed0a9ade8b693044cb7674", headers=h)
            >>> etag = rv.json()["data"]["etag"]
            >>> rv = delete(
            >>>          url + "/roles/5bed0a9ade8b693044cb7674?etag=" + etag,
            >>>          headers=h)
            >>> rv
            <Response [200]>
            >>> rv.json()
            {
                '_id': '5bed1134de8b6973711dc43b',
                'code': 200,
                'data': True,
                'message': 'OK',
                'timestamp': '2018-11-15T06:24:52.262685'
            }
        """
        if "/" in _id:
            _id, *e = _id.split("/")
            etag = self.parse_objectid("/".join(e))
        else:
            etag = self.get_argument("etag", as_type=ObjectId)
        oid = self.parse_objectid(_id)
        ret = await CoreRole().find_one(_id=oid)
        if ret is None:
            raise HTTPError(404, "role [%s] not found", oid)
        ret.data["etag"].set(etag)
        try:
            removed = await ret.delete()
        except (AttributeError, TypeError, core4.error.Core4ConflictError,
                core4.error.ArgumentParsingError) as exc:
            raise HTTPError(400, exc.args[0])
        except core4.error.Core4RoleNotFound as exc:
            raise HTTPError(404, "role [%s] not found", exc.args[0])
        except:
            raise
        else:
            if removed:
                self.reply(True)
            else:
                self.reply(False)
