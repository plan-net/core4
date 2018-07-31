# -*- coding: utf-8 -*-

import re

import pymongo

import core4.base
import core4.error
from core4.api.v1.role.field import *

ALPHANUM = re.compile('^[a-zA-Z0-9_.-]+$')
EMAIL = re.compile('^[_a-z0-9-]+(\.[_a-z0-9-]+)*'
                   '@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$')


class RoleField(Field):
    default = []

    def __init__(self, key, collection, **kwargs):
        self.collection = collection
        self.instance_id = []
        super().__init__(key, **kwargs)

    def _resolve(self, rid):
        doc = self.collection.find_one({"_id": rid})
        if doc is None:
            raise core4.error.Core4RoleNotFound(rid)
        return Role(**doc)

    def transform(self, value):
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
        return self.instance_id

    def _exists(self, _id):
        return self.collection.count({"_id": _id}) == 1


class Role(core4.base.CoreBase):
    """
    Access to core API, core jobs, databases and applications is managed through
    roles. Role data resides in core4 system collection ``sys.role``.
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
            # ("perm", PermField(_get("perm", []))),
            # ("last_login", TimestampField(_get("last_login"))),
            # ("token", TokenField(_get("token"))),
            # ("limit", LimitField(_get("limit")))
        ]

        self.data = dict([(f.key, f) for f in fields])

        for field in kwargs:
            if ((field not in self.data) and (field != "password_hash")):
                raise TypeError("unknown field [{}]".format(field))

    def __repr__(self):
        return "{}({})".format(
            self.qual_name(),
            ", ".join(["{}={}".format(k, repr(v.value))
                       for k, v in self.data.items()])
        )

    def __getattr__(self, item):
        if item in self.data:
            self.data.get(item).validate()
            return self.data.get(item).value
        return super().__getattribute__(item)

    def __setattr__(self, key, value):
        if "data" in self.__dict__:
            if key in self.__dict__["data"]:
                self.data[key].value = value
                return
        super().__setattr__(key, value)

    def create_index(self):
        self.config.sys.role.create_index(
            [("name", pymongo.ASCENDING)], unique=True)

    def save(self):
        self.create_index()
        for field in self.data.values():
            field.validate()
        self._check_circle()
        self._check_user()
        if self._id is None:
            return self._create()
        else:
            return self._update()

    def _check_user(self):
        have_password = self.password is not None
        have_email = self.email is not None
        if ((not (have_password and have_email))
                and (have_password or have_email)):
            raise AttributeError("user role requires email and password")

    def _check_circle(self):
        def traverse(r):
            for i in r:
                if i._id == self._id:
                    raise RuntimeError("circular roles")
                traverse(i.role)

        traverse(self.role)

    def _doc(self):
        doc = {}
        for k, f in self.data.items():
            val = f.to_mongo()
            if val is not None:
                doc[k] = val
        return doc

    def _create(self):
        self.data["created"].update()
        self.data["etag"].value = ObjectId()
        ret = self.config.sys.role.insert_one(self._doc())
        self.data["_id"].value = ret.inserted_id
        self.logger.info("created role [%s] with _id [%s]", self.name, self._id)
        return True

    def _update(self):
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
        self.logger.info("updated role [%s] with _id [%s]", self.name, self._id)
        return True

    def load(self, user=None, role=None, **kwargs):
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
        ret = self.load(*args, **kwargs)
        return next(ret)

    def verify_password(self, password):
        return self.data["password"].verify_password(password)

    def __eq__(self, other):
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
        return self.name < other.name

    def delete(self):
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
        self.logger.info("deleted role [%s] with _id [%s]", self.name, self._id)
        self._id = None
        self.etag = None

    def is_admin(self):
        return COP in self.perm

    def _job_access(self, qual_name):
        if self.is_admin():
            return True
        for p in self.perm:
            (*proto, qn, marker) = p.split("/")
            if re.match(qn, qual_name):
                return marker
        return None

    def has_job_access(self, qual_name):
        return self._job_access(qual_name) is not None

    def has_job_exec_access(self, qual_name):
        return self._job_access(qual_name) == JOB_EXECUTION_RIGHT

    def has_api_access(self, qual_name):
        if self.is_admin():
            return True
        for p in self.perm:
            (*proto, qn) = p.split("/")
            if re.match(qn, qual_name):
                return True
        return False
