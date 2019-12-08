#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
This module delivers the :class:`.CoreRole` to manage users and roles.
"""

import json

import core4.error
import core4.util.crypt
import core4.util.node
from core4.api.v1.request.role.field import *
from core4.base.main import CoreBase

ALPHANUM = re.compile(r'^[a-zA-Z0-9_.-]+$')
EMAIL = re.compile(r'^[_a-z0-9-]+(\.[_a-z0-9-]+)*'
                   r'@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$')


class CoreRole(CoreBase):
    """
    Implements all users and roles. Users differ from roles with two requires
    properties: an ``email`` and a ``password``. For roles both properties
    must be empty/``None``.

    Users and roles have the following properties:

    * ``_id`` (ObjectId) - MongoDB identifier
    * ``name`` (str) - short name (must be unique, only characters, numbers,
      underscore, dot and hyphen)
    * ``realname`` (str) - long/real name
    * ``is_active`` (bool)
    * ``created`` (datetime) - when the role has been created
    * ``updated`` (datetime) - when the role has been last updated
    * ``etag`` (ObjectId) - concurrency control with update and delete
    * ``role`` (list) - of assigned roles
    * ``email`` (str) - applies only to users and requires a password field
    * ``password`` (str) - applies only to users and requires an email field
    * ``perm`` (list) - of permissions
    * ``last_login`` (datetime) - automatically updated at login

    Note that roles can be assigned hierarchically.

    Raises:
        KeyError - unknown role attribute
        AttributeError - email requires password and vice versa
        Core4RoleNotFound - unknown role
        RuntimeError - database error
        Core4ConflictError - concurrent update/delete
        ArgumentParsingError - role must be loaded before delete
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
            RoleField("role", **kwargs),
            StringField("email", regex=EMAIL, **kwargs),
            PasswordField("password", **kwargs),
            PermField("perm", **kwargs),
            TimestampField("last_login", **kwargs),
            # QuotaField("quota", **kwargs),
        ]
        self.data = dict([(f.key, f) for f in fields])
        for field in kwargs:
            if (field not in self.data):
                raise KeyError("unknown field [{}]".format(field))
        self._role_collection = None
        self._casc_role = None

    @property
    def role_collection(self):
        """
        :return: async :class:`.CoreCollection` object to ``sys.role``
        """
        if self._role_collection is None:
            self._role_collection = self.config.sys.role.connect_async()
        return self._role_collection

    def __getattr__(self, item):
        """
        forward role attribute getter to field values.
        """
        if item in self.data:
            return self.data.get(item).value
        return super().__getattribute__(item)

    def __setattr__(self, key, value):
        """
        forward role attribute setter to field values.
        """
        if "data" in self.__dict__:
            if key in self.__dict__["data"]:
                self.data[key].value = value
                return
        super().__setattr__(key, value)

    def __eq__(self, other):
        """
        Compares the role with the ``other`` role. Two roles are equal if all
        attributes are equal except ``created`` and ``updated``.
        """
        if other is None:
            return False
        self_doc = self.to_doc()
        other_doc = other.to_doc()
        for k in ["created", "updated"]:
            self_doc.pop(k, None)
            other_doc.pop(k, None)
        return self_doc == other_doc

    def __lt__(self, other):
        """
        Compares the role with the ``other`` role. This comparison operation is
        solely based on the ``.name`` attribute of the two roles.
        """
        return self.name.lower() < other.name.lower()

    def validate(self, initial=False):
        """
        Ensures users have email *and* password, and all field have the
        expected types and value constraints.
        """
        self._check_user(initial)
        for field in self.data.values():
            field.validate_type()
            field.validate_value()

    def verify_password(self, plain):
        """
        :param plain: clear text password
        :return: ``True`` if the role is active , and the password matches
        """
        if self.is_active:
            try:
                self._check_user()
                return core4.util.crypt.pwd_context.verify(
                    plain, self.password)
            except ValueError:
                self.logger.warning("user [%s] authentication failure",
                                    self.name)
                return False
            except AttributeError:
                return False
            except:
                raise
        self.logger.warning("user [%s] not active", self.name)
        return False

    @property
    def is_user(self):
        """
        :return: ``True`` if the role is a user with email and password.
        """
        has_password = self.password is not None
        has_email = self.email is not None
        return has_email and has_password

    def _check_user(self, initial=False):
        """
        :return: verify a valid role (no email and password) or a valid
                 user role (email and password).
                 When the user is initialy created, he does not need a password
                 yet. It will be set prior to logging in via a token provided
                 by email.
        """
        has_password = self.password is not None
        has_email = self.email is not None
        if initial:
            if not (has_email == has_password or has_email):
                raise AttributeError("user role requires email on creation")
        elif ((not (has_password and has_email))
                and (has_password or has_email)):
            raise AttributeError("user role requires email and password")

    async def save(self, initial=False):
        """
        Create or update the role. Please note that a role is only
        materialised, if one or more attributes have changed.

        :return: ``True`` if the role has been updated, else ``False``.
        """
        # await self.create_index()
        await self.resolve_roles()
        self.validate(initial)
        if self._id is None:
            saved = await self._create()
        else:
            saved = await self._update()
        # if saved:
        #     self.data["quota"].insert(self.config.sys.quota, self._id)
        return saved

    async def resolve_roles(self, by_id=False):
        """
        Extends :class:`.RoleField` properties ``.name`` with roles' name
        and/or ``._id`` with roles' MongoDB ``_id``.

        :param by_id: ``True`` to search in ``.role`` by ``id``, else by
                      ``name`` (default)
        """
        _ids = []
        names = []
        if by_id:
            search_key = "_id"
        else:
            search_key = "name"

        for _id in sorted(set(self.role)):
            obj = await CoreRole._find_one(**{search_key: _id})
            if obj is None:
                raise core4.error.Core4RoleNotFound(_id)
            _ids.append(obj._id)
            names.append(obj.name)
        self.data["role"].name = names
        self.data["role"]._id = _ids

    async def resolve_roles_by_id(self):
        """
        Extends :class:`.RoleField` properties ``.name`` with roles' name and
        ``._id`` with roles' MongoDB ``_id``. The analysis is based on roles'
        ``_id``
        """
        await self.resolve_roles(by_id=True)
        self.data["role"].value = self.data["role"].name[:]

    async def _create(self):
        """
        Internal method used to create the role.

        Raises :class:`RuntimeError` in case of any unexpected error.
        """
        self.created = core4.util.node.mongo_now()
        self.data["etag"].set(ObjectId())
        ret = await self.role_collection.insert_one(self.to_doc())
        if ret.inserted_id is None:
            raise RuntimeError("failed to insert role [{}]".format(self.name))
        self._id = ret.inserted_id
        self.logger.info("created role [%s] with _id [%s]", self.name,
                         self._id)
        return True

    async def _update(self):
        """
        Internal method used to update the role.

        Raises :class:`.Core4RoleNotFound`-
        """
        try:
            test = await self.find_one(_id=self._id)
        except StopIteration:
            raise core4.error.Core4RoleNotFound(
                "role [{}] with _id [{}] not found".format(
                    self.name, self._id))
        if test == self:
            self.logger.info("skipped update of role [%s] with _id [%s]",
                             self.name, self._id)
            return False
        self.updated = core4.util.node.mongo_now()
        curr_etag = self.etag
        self.data["etag"].set(ObjectId())
        doc = self.to_doc()
        ret = await self.role_collection.update_one(
            filter={"_id": self._id, "etag": curr_etag},
            update={"$set": doc})
        if ret.matched_count == 0:
            raise core4.error.Core4ConflictError(
                "update [{}] with etag [{}] failed".format(
                    self._id, curr_etag))
        self.logger.info("updated role [%s] with _id [%s]", self.name,
                         self._id)
        return True

    def to_doc(self, response=False):
        """
        Translates the role attributes into a Python dict.

        :param response: translate into dict ready for MongoDB (``False``) or
                         for request response (``True``). Defaults to ``False``
        :return: dict
        """
        doc = {}
        for k, f in self.data.items():
            if response:
                val = f.to_response()
            else:
                val = f.to_doc()
            if val is not None:
                doc[k] = val
        return doc

    def to_response(self):
        """
        Translates the role attributes into a Python dict, removes the password
        and returns the document to be sent to the client.

        :return: dict ready for request response
        """
        doc = self.to_doc(response=True)
        doc.pop("password", None)
        return doc

    async def load(self, skip=0, limit=0, filter={}, sort_by=("_id", 1)):
        """
        Retrieve a list of roles in the specified sort order applying optional
        search filters. This method uses core4's :class:`.CorePager`.

        :param skip: number of documents to skip
        :param sort_by: tuple of attribute and sort order (``1`` for ascending,
                        ``-1`` for descending)
        :param filter: MongoDB query dict
        :param limit: number of records to be retrieved
        :return: :list: resulting documents
        """
        filter = await self.manage_filter(filter)

        cur = self.role_collection.find(filter) \
            .sort(*sort_by) \
            .skip(skip) \
            .limit(limit)

        # None will exhaust the whole cursor. no buffering needed here.
        return await cur.to_list(length=None)

    async def load_one(self, **kwargs):
        """
        Loads the first matching role from the mongo database. For ``*args``
        and ``**kwargs`` see :meth:`.load`.

        :return: dict of user/role attributes
        """
        ret = await self.load(filter=kwargs)
        if ret:
            return ret[0]
        return None

    async def count(self, filter={}):
        filter = await self.manage_filter(filter)
        return await self.role_collection.count_documents(filter)

    @classmethod
    async def _find_one(cls, **kwargs):
        doc = await CoreRole().load_one(**kwargs)
        if doc:
            password = doc.pop("password", None)
            role = CoreRole(**doc)
            role.data["password"].__dict__["value"] = password
            return role
        return None

    @classmethod
    async def find_one(cls, **kwargs):
        """
        Retrieve one role using the filtering attributes of :meth:`.load_one`.

        :param query_filter: MongoDB query dict
        :param user: if ``True`` retrieves only user roles with email and
                     password
        :param role: if ``True`` retrieves only roles without email and
                     password
        :return: first :class:`.CoreRole` matching the search criteria
        """
        role = await cls._find_one(**kwargs)
        if role is not None:
            await role.resolve_roles_by_id()
        return role

    async def casc_perm(self):
        """
        Retrieve combined permissions from all roles assigned.

        :return: list of permission str
        """
        perm = self.perm
        for role in await self.casc_role():
            perm += role.perm
        return sorted(list(set(perm)))

    async def casc_role(self):
        """
        Retrieve combined role names from all roles assigned.

        :return: list of role names (str)
        """

        if self._casc_role is None:
            seen = []

            async def traverse(_ids, roles):
                for _id in _ids:
                    if _id in seen:
                        continue
                    seen.append(_id)
                    role = await self.find_one(_id=_id)
                    if role.is_active:
                        roles += [role]
                        await traverse(role.data["role"]._id, roles)

            self._casc_role = []
            await traverse(self.data["role"]._id, self._casc_role)

        return self._casc_role

    async def delete(self):
        """
        Deletes the role.

        This method raises :class:`.Core4ConflictError` if the role has been
        updated in between.
        """
        if not self._id:
            raise core4.error.ArgumentParsingError("Role object not loaded")
        # delete the role
        ret = self.config.sys.role.delete_one(
            {"_id": self._id, "etag": self.etag})
        if ret.deleted_count == 0:
            raise core4.error.Core4ConflictError(
                "update [{}] with etag [{}] failed".format(
                    self._id, self.etag))
        # delete references
        self.config.sys.role.update_many({}, update={
            "$pull": {
                "role": self._id
            }
        })
        self.logger.info("deleted role [%s] with _id [%s]", self.name,
                         self._id)
        self._id = None
        self.data["etag"].set(None)
        return True

    async def _job_access(self, qual_name, access):
        # verify access (r|x) to the passed qual_name
        if await self.is_admin():
            return True
        for p in await self.casc_perm():
            (*proto, qn, acc) = p.split("/")
            if proto[0] == "job:":
                if re.match(qn, qual_name):
                    if acc.lower() in access:
                        return True
        return False

    async def has_job_access(self, qual_name):
        """
        Verify read/execute access to the passed job ``qual_name``
        :param qual_name: of the job

        :return: ``True`` if the user has access, else ``False``
        """
        return await self._job_access(
            qual_name, (JOB_EXECUTION_RIGHT, JOB_READ_RIGHT))

    async def has_job_exec_access(self, qual_name):
        """
        Verify execute access to the passed job ``qual_name``

        :param qual_name: of the job
        :return: ``True`` if the user has access, else ``False``
        """
        return await self._job_access(
            qual_name, (JOB_EXECUTION_RIGHT))

    async def is_admin(self):
        """
        :return: ``True`` if the role as a ``perm`` record of ``cop``.
        """
        return COP in await self.casc_perm()

    async def has_api_access(self, qual_name):
        """
        Verifies the passed ``qual_name`` matches any ``api://`` permission
        of the role.

        :param qual_name: to verify
        :return: bool
        """
        if await self.is_admin():
            return True
        for p in await self.casc_perm():
            (*proto, qn) = p.split("/")
            if proto[0] == "api:":
                if re.match(qn, qual_name):
                    self.logger.debug(
                        "approved api permission [%s] for user [%s]",
                        self.name, qn)
                    return True
        self.logger.debug("no appropriate api permission found for user [%s]",
                          self.name)
        return False

    async def has_client_access(self, client):
        """
        Verifies the user has a valid permission ``app://client/[client-name]``.

        :param client: client (str) extracted from the URL
        :return: ``True`` for success, else ``False``
        """
        if await self.is_admin():
            return True
        for p in await self.casc_perm():
            parts = p.split("/")
            if len(parts) > 3:
                if parts[0] == "app:":
                    if parts[2] == "client":
                        if "/".join(parts[3:]) == client:
                            self.logger.debug("grant access to client [%s]",
                                              client)
                            return True
        return False

    async def login(self):
        """
        Updates the ``last_login`` attribute of the role-

        This method raises :class:`.Core4ConflictError` if the role has been
        updated in between.
        """
        self.last_login = core4.util.node.mongo_now()
        ret = await self.role_collection.update_one(
            filter={"_id": self._id, "etag": self.etag},
            update={"$set": {"last_login": self.last_login}})
        if ret.matched_count == 0:
            raise core4.error.Core4ConflictError(
                "update [{}] with etag [{}] failed".format(
                    self._id, self.etag))
        self.logger.info("set [last_login] for role [%s] with _id [%s]",
                         self.name, self._id)

    async def detail(self):
        """
        Converts role attributes into a response (see :meth:`.to_response` and
        cascaedes the role's permission and role names (see :meth:`.casc_perm`
        and :meth:`.casc_role`.

        :return: dict
        """
        doc = self.to_response()
        doc["perm"] = sorted(await self.casc_perm())
        doc["role"] = sorted([r.name for r in await self.casc_role()
                              if r.name != self.name])
        return doc

    async def manage_filter(self, filter):
        """
        If given a dict by backend, returns that dict. If given a string:
        * is the string a dict representation: try to convert
        * if not, assume its full text search

        Pass regex handling to :meth: `.manage_dict_filter`.

        :param filter: query string
        :return: mongodb query filter
        """
        if filter and isinstance(filter, str):
            if filter.startswith("{") and filter.endswith("}"):
                try:
                    query_filter = json.loads(filter)
                    query_filter = await self.manage_dict_filter(query_filter)
                except:
                    raise core4.error.ArgumentParsingError(
                        "Can not parse regex" + filter)
                filter = query_filter
            else:
                filter = re.compile(filter)
                query_filter = \
                    {
                        "$or": [
                            {"name": {"$regex": filter, '$options': 'i'}},
                            {"realname": {"$regex": filter, '$options': 'i'}},
                            {"perm": {"$regex": filter, '$options': 'i'}}
                        ]
                    }
                filter = query_filter
        return filter

    async def manage_dict_filter(self, filter={"_id": ".*"}):
        """
        Takes a given dict and translates it to a mongodb query dict.
        Will compile strings to regex where needed.

        It does not try to convert types, so:
        "True" or "False" will still be strings.

        :param filter: query dict
        :return: mongodb query dict.
        """
        for k, v in filter.items():
            if isinstance(v, str):
                if re.match("^[a-zA-Z0-9_/-]*$", v):
                    pass
                else:
                    filter[k] = re.compile(v)
            elif isinstance(v, dict):
                filter[k] = await self.manage_dict_filter(v)
            elif isinstance(v, list):
                tmpl = []
                for i in v:
                    tempitem = await self.manage_dict_filter({"j": i})
                    tmpl.append(tempitem["j"])
                filter[k] = tmpl
        return filter

    async def distinct_roles(self):
        return await self.role_collection.distinct("name")
