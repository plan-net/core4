# -*- coding: utf-8 -*-

import re

import datetime
import pymongo
import pymongo.errors
from bson.objectid import ObjectId

import core4.base
import core4.error
import core4.util
from werkzeug.security import generate_password_hash, check_password_hash
import re
from flask_login import login_user

COP = "cop"
ALPHANUM = re.compile('^[a-zA-Z0-9_.-]+$')
EMAIL = re.compile('^[_a-z0-9-]+(\.[_a-z0-9-]+)*'
                   '@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$')

PROTO = [
    COP,
    re.compile("^{}$".format(COP)),
    re.compile("^job://[^\s]+/[xr]$"),
    re.compile("^api://[^\s]+$"),
    re.compile("^app://[^\s]+$"),
    re.compile("^mongodb://[^\s]+$")
]

JOB_EXECUTION_RIGHT = 'x'
JOB_READ_RIGHT = 'r'


class Role(core4.base.CoreBase):
    """
    Access to core API, core jobs, databases and applications is managed through
    roles. Role data resides in core4 system collection ``sys.role``.
    """

    def __init__(self, **kwargs):
        super().__init__()
        self.data = {
            "_id": None,
            "rolename": None,
            "realname": None,
            "is_active": True,
            "created": None,
            "updated": None,
            "etag": None,
            "role": [],
            "perm": []
        }
        for (attr, default) in self.data.items():
            val = kwargs.get(attr, default)
            if isinstance(val, str):
                val = val.strip()
            self.data[attr] = val
        roles = []
        for role in self.role:
            roles.append(self._resolve(role))
        self.data["role"] = roles

    def validate(self):
        if self._id is not None:
            if not isinstance(self._id, ObjectId):
                raise TypeError(
                    "_id requires bson.objectid.ObjectId")
        if not isinstance(self.rolename, str):
            raise TypeError("rolename requires str")
        if ALPHANUM.match(self.rolename) is None:
            raise TypeError("rolename must match [a-zA-Z0-9_.-]")
        if not isinstance(self.realname, str):
            raise TypeError("realname requires str")
        if not isinstance(self.is_active, bool):
            raise TypeError("is_active requires bool")
        if not isinstance(self.etag, ObjectId):
            raise TypeError("etag requires bson.objectid.ObjectId")
        if not isinstance(self.perm, list):
            raise TypeError("perm requires list")
        # if self.password is not None:
        #     if not isinstance(self.password, str):
        #         raise TypeError("password requires str")
        #     if self.email is None:
        #         raise AttributeError("password requires an email, too")
        # if self.email is not None:
        #     if not isinstance(self.email, str):
        #         raise TypeError("email requires str")
        #     if EMAIL.match(self.email) is None:
        #         raise TypeError("invalid email address")
        #     if self.password is None:
        #         raise AttributeError("email requires a password, too")
        for p in self.perm:
            passed = False
            for t in PROTO:
                if re.match(t, p) is not None:
                    passed = True
                    break
            if not passed:
                raise TypeError("invalid perm protocol [{}]".format(p))

    def __repr__(self):
        return "%s(%s)" % (
            self.qual_name(),
            ", ".join(["{}={}".format(
                i, repr(v)) for (i, v) in self.data.items()]))

    def create_index(self):
        self.config.sys.role.create_index(
            [("rolename", pymongo.ASCENDING)], unique=True)

    def save(self):
        self.create_index()
        roles = []
        ids = []
        for role in self.role:
            r = role
            if isinstance(r, Role):
                if r._id is None:
                    raise RuntimeError("role [{}] not found".format(r.rolename))
            else:
                r = self._resolve(r)
            ids.append(r._id)
            roles.append(r)

        def traverse(r, level=0):
            for i in r:
                if i._id == self._id:
                    raise RuntimeError("circular roles")
                traverse(i.role, level + 1)

        traverse(roles)

        if self.data["_id"] is None:
            return self._create(ids)
        return self._update(ids)

    def _create(self, ids):
        if self.data["etag"] is not None:
            raise core4.error.Core4ConflictError(
                "update failed, role has been removed"
            )
        self.data["created"] = core4.util.now()
        doc = self._get_doc(ids)
        self.validate()
        ret = self.config.sys.role.insert_one(doc)
        self.data["_id"] = ret.inserted_id
        return True

    def _get_doc(self, ids):
        self.data["etag"] = ObjectId()
        doc = self.data.copy()
        _id = doc["_id"]
        del doc["_id"]
        doc["role"] = ids
        # if doc["password"] is not None:
        #     doc["password"] = generate_password_hash(doc["password"])
        # del doc["password_hash"]
        return doc

    def _update(self, ids):
        curr_etag = self.data["etag"]
        test = self.load_one(_id=self._id)
        if test == self:
            return False
            self.data["updated"] = core4.util.now()
        self.validate()
        doc = self._get_doc(ids)
        ret = self.config.sys.role.update_one(
            filter={"_id": self.data["_id"], "etag": curr_etag},
            update={"$set": doc})
        if ret.matched_count == 0:
            raise core4.error.Core4ConflictError(
                "update [{}] with etag [{}] failed".format(
                    self._id, curr_etag))
        return True

    def load(self, **kwargs):
        cur = self.config.sys.role.find(filter=kwargs, sort=[("rolename", 1)])
        for rec in cur:
            # rec["password_hash"] = rec["password"]
            # del rec["password"]
            yield Role(**rec)

    def _resolve(self, role):
        if isinstance(role, ObjectId):
            return self.load_one(_id=role)
        elif isinstance(role, Role):
            return self.load_one(_id=role._id)
        return self.load_one(rolename=role)

    def load_one(self, **kwargs):
        ret = list(self.load(**kwargs))
        if ret:
            return ret[0]
        return None

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
                "role": self.data["_id"]
            }
        })
        # mark deleted
        self.data["_id"] = None

    # @property
    # def is_authenticated(self):
    #     return True
    #
    # @property
    # def is_anonymous(self):
    #     return False
    #
    # def get_id(self):
    #     return str(self._id)

    def __getattr__(self, item):
        if item in self.data:
            return self.data.get(item)
        return super().__getattribute__(item)

    def __lt__(self, other):
        return self.rolename < other.rolename

    def __eq__(self, other):
        if other is None:
            return False
        self_doc = self.data.copy()
        other_doc = other.data.copy()
        for k in ["created", "updated"]:
            del self_doc[k]
            del other_doc[k]
        return self_doc == other_doc

    # def is_admin(self):
    #     """
    #     :return: ``True`` if the role has admin rights
    #     """
    #     return self.is_active and (COP in self.perm)

    def __setattr__(self, key, value):
        if "data" in self.__dict__:
            if key in self.__dict__["data"]:
                self.data[key] = value
                return
        super().__setattr__(key, value)

    # def login(self):
    #     """
    #     :return: ``True`` for success, else ``False``
    #     """
    #     # token = current_app.api.serializer.dumps(
    #     #     {
    #     #         'username': self.username,
    #     #         'random': str(uuid.uuid4())
    #     #     }
    #     # )
    #     # self.token = token
    #     # self.save()
    #     return login_user(self, remember=False)
    #
    # def verify_password(self, password):
    #     if self.password_hash is not None:
    #         return check_password_hash(self.password_hash, password)
    #     return False
