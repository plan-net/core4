# -*- coding: utf-8 -*-

"""
This module provides class :class:`.Role` featuring authorisation and access
management to core4 API, jobs, databases and applications.

Instantiate and save a new role with::

    role = Role(name="test", realname="Test Role", email="test@mail.com",
                password="secret")
    role.save()

Load an existing role with::

    role = Role().load_one(name="test")
"""

import pymongo
from flask_login import login_user

import core4.base
import core4.error
from core4.api.v1.role.field import *

ALPHANUM = re.compile(r'^[a-zA-Z0-9_.-]+$')
EMAIL = re.compile(r'^[_a-z0-9-]+(\.[_a-z0-9-]+)*'
                   r'@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$')


class Role(core4.base.CoreBase):
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

    def __repr__(self):
        return "{}({})".format(
            self.qual_name(),
            ", ".join(["{}={}".format(k, repr(v.value))
                       for k, v in self.data.items()])
        )

    def __getattr__(self, item):
        """
        forward role attribute getter to fields
        """
        if item in self.data:
            self.data.get(item).validate()
            return self.data.get(item).value
        return super().__getattribute__(item)

    def __setattr__(self, key, value):
        """
        forward role attribute setter to fields
        """
        if "data" in self.__dict__:
            if key in self.__dict__["data"]:
                self.data[key].value = value
                if key in ["perm", "role"]:
                    self._perm = None
                return
        super().__setattr__(key, value)

    def create_index(self):
        """
        Internal method used to create a unique index on the ``name``
        attribute
        """
        self.config.sys.role.create_index(
            [("name", pymongo.ASCENDING)], unique=True, name="unique_name")
        self.config.sys.role.create_index(
            [("email", pymongo.ASCENDING)], unique=True, name="unique_email",
            partialFilterExpression={"email": { "$exists": True}})

    def save(self):
        """
        Create and update the role. Please note that a role is only
        materialised, if one or more attributes have changed.

        This method raises :class:`.Core4ConflictError` if the role has been
        updated in between, :class:`RuntimeError` in case of circular roles,
        :class:`AttributeError` if an email but no password has been specified
        (and vice verse) or any field validation failed.

        :return: ``True`` if the role has been updated, else ``False``.
        """
        self.create_index()
        for field in self.data.values():
            field.validate()
        self._check_circle()
        self._check_user()
        if self._id is None:
            saved = self._create()
        else:
            saved = self._update()
        if saved:
            self.data["quota"].insert(self.config.sys.quota, self._id)
        return saved

    def _check_user(self):
        """
        :return: verify a valid role (no email and password) or a valid
                 user role (email and password)
        """
        have_password = self.password is not None
        have_email = self.email is not None
        if ((not (have_password and have_email))
                and (have_password or have_email)):
            raise AttributeError("user role requires email and password")

    def _check_circle(self):
        """
        Verify no circular roles are defined, raises :class:`RuntimeError`.
        """

        def traverse(r):
            for i in r:
                if i._id == self._id:
                    raise RuntimeError("circular roles")
                traverse(i.role)

        traverse(self.role)

    def _doc(self):
        """
        Transforms the role object into a valid MongoDB document.
        """
        doc = {}
        for k, f in self.data.items():
            val = f.to_mongo()
            if val is not None:
                doc[k] = val
        return doc

    def _create(self):
        """
        Internal method used to create the role.
        """
        self.data["created"].update()
        self.data["etag"].value = ObjectId()
        ret = self.config.sys.role.insert_one(self._doc())
        self.data["_id"].value = ret.inserted_id
        self.logger.info("created role [%s] with _id [%s]", self.name,
                         self._id)
        return True

    def _update(self):
        """
        Internal method used to update the role.
        """
        try:
            test = self.load_one(_id=self._id)
        except StopIteration:
            raise RuntimeError("role [{}] with _id [{}] not found".format(
                self.name, self._id))
        if test == self:
            self.logger.debug("skipped update of role [%s] with _id [%s]",
                              self.name, self._id)
            return False
        self.data["updated"].update()
        curr_etag = self.etag
        self.etag = ObjectId()
        doc = self._doc()
        ret = self.config.sys.role.update_one(
            filter={"_id": self._id, "etag": curr_etag},
            update={"$set": doc})
        if ret.matched_count == 0:
            raise core4.error.Core4ConflictError(
                "update [{}] with etag [{}] failed".format(
                    self._id, curr_etag))
        self.logger.info("updated role [%s] with _id [%s]", self.name,
                         self._id)
        return True

    def load(self, user=None, role=None, **kwargs):
        """
        Generator loading the roles from the mongo database.

        :param user: if ``True``, then only roles with an email will be
                     retrieved
        :param role: if ``True`` then only roles without email will be
                     retrieved
        :param kwargs: query parameters to filter role retrieval

        :return: generator of :class:`Role`
        """
        if ((user or role) and (not (user and role))):
            if user:
                kwargs["email"] = {"$exists": True}
            if role:
                kwargs["email"] = {"$exists": False}
        cur = self.config.sys.role.find(filter=kwargs, sort=[("name", 1)])
        for rec in cur:
            if "password" in rec:
                rec["password_hash"] = rec["password"]
                del rec["password"]
            yield Role(**rec)

    def load_one(self, *args, **kwargs):
        """
        Loads the first matching role from the mongo database. For ``*args``
        and ``**kwargs`` see :meth:`.load`.

        :return: first :class:`.Role` matching the search criteria
        """
        ret = self.load(*args, **kwargs)
        return next(ret)

    def __eq__(self, other):
        """
        Compares the role with the passed ``other`` role. Two roles are equal
        if all attributes are equal.
        """
        if other is None:
            return False
        self_doc = self._doc()
        other_doc = other._doc()
        for k in ["created", "updated"]:
            if k in self_doc:
                del self_doc[k]
            if k in other_doc:
                del other_doc[k]
        return self_doc == other_doc

    def __lt__(self, other):
        """
        Compares the role with the passed ``other`` role. This comparison
        operation is solely based on the ``.name`` attribute of the two roles.
        """
        return self.name < other.name

    def delete(self):
        """
        Deletes the role.

        This method raises :class:`.Core4ConflictError` if the role has been
        updated in between.
        """
        if not self._id:
            raise RuntimeError("Role object not loaded")
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
        self.etag = None

    @property
    def _casc_perm(self):
        """
        Internal method to recurively collect all permissions
        (:class:`.PermField`).
        """
        if self._perm is None:

            def traverse(role):
                p = role.perm[:]
                for i in role.role:
                    p += traverse(i)
                return p

            perm = traverse(self)
            perm = list(set(perm))
            perm.sort()
            self._perm = perm
        return self._perm

    @property
    def is_admin(self):
        """
        :return: ``True`` if the role as a ``perm`` record of ``cop``.
        """
        return COP in self._casc_perm

    def _job_access(self, qual_name):
        """
        Internal method to check job access permissions.
        """
        if self.is_admin:
            return True
        for p in self._casc_perm:
            (*proto, qn, marker) = p.split("/")
            if re.match(qn, qual_name):
                return marker
        return None

    def has_job_access(self, qual_name):
        """
        :param qual_name: of the job, see :meth:`.qual_name`
        :return: ``True`` if the role has read and/or execution access
                 permissions, else ``False``
        """
        return self._job_access(qual_name) is not None

    def has_job_exec_access(self, qual_name):
        """
        :param qual_name: of the job, see :meth:`.qual_name`
        :return: ``True`` if the role has execution access permissions, else
                 ``False``
        """
        return self._job_access(qual_name) == JOB_EXECUTION_RIGHT

    def has_api_access(self, qual_name):
        if self.is_admin:
            return True
        for p in self._casc_perm:
            (*proto, qn) = p.split("/")
            if re.match(qn, qual_name):
                return True
        return False

    def login(self):
        """
        :return: ``True`` for success, else ``False``
        """
        self.last_login = core4.util.now()
        self.config.sys.role.update_one(
            {"_id": self._id}, {"$set": {"last_login": self.last_login}})
        self.logger.info("login user [%s] with _id [%s]", self.name, self._id)
        return login_user(self, remember=False)

    def verify_password(self, password):
        """
        :param password: in clear text
        :return: ``True`` if the password matches the stored password hash
        """
        return self.data["password"].verify_password(password)

    def get_id(self):
        """
        :return: role ``_id`` as str
        """
        return str(self._id)

    def dec_quota(self):
        """
        This method decreases the role`s rate limit.

        :return: ``True`` if the role is in the defined rate limit, else
                 ``False``
        """
        # regular quota update
        now = core4.util.now()
        upd = self.config.sys.quota.update_one(
            filter={
                "_id": self._id,
                "timestamp": {
                    "$gt": now
                },
                "current": {
                    "$gt": 0
                }
            },
            update={
                "$inc": {
                    "current": -1
                }
            }
        )
        if upd.modified_count == 0:
            # next interval
            upd = self.config.sys.quota.update_one(
                filter={
                    "_id": self._id,
                    "$or": [
                        {
                            "timestamp": None
                        },
                        {
                            "timestamp": {
                                "$lt": now
                            }
                        }
                    ]
                },
                update={
                    "$set": {
                        "current": self.data["quota"].limit - 1,
                        "timestamp": now + datetime.timedelta(
                            seconds=self.data["quota"].seconds)
                    }
                }
            )
            if upd.modified_count == 0:
                return False
        return True


class RoleField(Field):
    """
    This class handles the ``role`` attribute of a role. By assigning one or
    more roles to a role, the permissions of these roles (see
    :class:`.PermField`) are inherited. This allows to define hierarchical
    access permissions.
    """
    default = []

    def __init__(self, key, collection, **kwargs):
        self.collection = collection
        self.instance_id = []
        super().__init__(key, **kwargs)

    def _resolve(self, rid):
        """
        Internal method to load roles by the role ``_id``.
        """
        doc = self.collection.find_one({"_id": rid})
        if doc is None:
            raise core4.error.Core4RoleNotFound(rid)
        return Role(**doc)

    def transform(self, value):
        """
        Verify the value type as a list of role ``_id`` or :class:`.Role`
        objects.
        """
        error = False
        if not isinstance(value, list):
            error = True
        else:
            ids = []
            obj = []
            for r in value:
                i = None
                o = None
                if isinstance(r, ObjectId):
                    i = r
                    o = self._resolve(r)
                elif isinstance(r, Role):
                    i = r._id
                    o = r
                else:
                    error = True
                if i not in ids:
                    if not self._exists(i):
                        error = True
                    else:
                        ids.append(i)
                        obj.append(o)
        if error:
            raise TypeError(
                "field [{}] requires list of existing ObjectId".format(
                    self.key))
        self.instance_id = ids
        return obj

    def to_mongo(self):
        """
        This method is executed to translate the role objects into valid
        :class:`.ObjectId`.
        """
        return self.instance_id

    def _exists(self, _id):
        """
        Internal method used to check if the role ``_id`` exists.
        """
        return self.collection.count({"_id": _id}) == 1
