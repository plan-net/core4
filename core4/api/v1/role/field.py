# -*- coding: utf-8 -*-

"""
This module delivers the :class:`.Role` field types.
"""

import re

import datetime
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

import core4.util

COP = "cop"
PROTO = [
    re.compile(r"^" + COP + "$"),
    re.compile(r"^job://[^\s\/]+/[xr]$"),
    re.compile(r"^api://[^\s\/]+$"),
    re.compile(r"^app://[^\s]+$"),
    re.compile(r"^mongodb://[^\s]+$")
]
JOB_EXECUTION_RIGHT = 'x'
JOB_READ_RIGHT = 'r'
LIMIT = re.compile(r"^\s*(\d+)\s*\D\s*(\d+)\s*$")


class Field:
    """
    This is the base class of all :class:`.Role` attributes.
    """

    default = None

    def __init__(self, key, **kwargs):
        super().__init__()
        self.key = key
        self.value = kwargs.get(self.key, self.default)

    def validate(self):
        """
        Field validation is performed before :meth:`.save`.

        :return: ``True`` in case of success, else ``False``
        """
        return True

    def transform(self, value):
        """
        Field transformation is performed before setting the attribute.

        :param value: original value
        :return: transformed value
        """
        raise NotImplementedError()  # pragma: no cover

    def to_mongo(self):
        """
        This method is executed to translate the attribute into a valid
        MongoDB field.

        :return: translated attribute value
        """
        return self.value

    def __setattr__(self, key, value):
        if key == "value":
            value = self.transform(value)
        super().__setattr__(key, value)


class ObjectIdField(Field):
    """
    This class handles role ``_id`` and ``etag`` attribute and verifies the
    value is of type :class:`.ObjectId``.
    """

    def transform(self, value):
        if not (value is None or isinstance(value, ObjectId)):
            raise TypeError("field [{}] requires ObjectId".format(self.key))
        return value


class StringField(Field):
    """
    This class handles role string attributes. Additional attribute properties
    are ``required`` to indicate non-optional fields and ``regex`` to perform
    value validation.
    """

    def __init__(self, key, required=False, regex=None, **kwargs):
        self.required = required
        self.regex = regex
        super().__init__(key, **kwargs)

    def validate(self):
        """
        Verify the ``required`` attributes.
        """
        if self.required:
            if self.value is None or self.value.strip() == "":
                raise TypeError("field [{}] is mandatory".format(self.key))
        return True

    def transform(self, value):
        """
        Verify value type and the optional ``regex`` attribute, if defined.
        """
        if not (value is None or isinstance(value, str)):
            raise TypeError("field [{}] requires str".format(self.key))
        if value is not None:
            value = value.strip()
            if self.regex is not None:
                if not self.regex.match(value) is not None:
                    raise TypeError("field [{}] must match [{}]".format(
                        self.key, self.regex.pattern))
        return value


class BoolField(Field):
    """
    This class handles bool attributes.
    """
    default = True

    def transform(self, value):
        """
        Verify value type
        """
        if not (isinstance(value, bool)):
            raise TypeError("field [{}] requires bool".format(self.key))
        return value


class TimestampField(Field):
    """
    This class handles :class:`.datetime` attributes. The class provides an
    extra method :meth:`.update` to set the value to the current time in UTC.
    """

    def transform(self, value):
        """
        Verify value type
        """
        if not (value is None
                or isinstance(value, datetime.datetime)):
            raise TypeError("field [{}] requires datetime".format(self.key))
        return value

    def update(self):
        """
        Set the value to current date/time in UTC.
        """
        self.value = core4.util.now()


class PermField(Field):
    """
    This class handles role ``perm`` attribute. This attribute is a list of
    strings with the following permission protocols:

    * ``cop`` - administrative role
    * ``job://[qual_name]/[xr]`` - job read and execution permission
    * ``api://[qual_name]`` - api access permission
    * ``app://[key]`` - app key definition
    * ``mongodb://[database]`` - MongoDB database access permission (read-only)
    """
    default = []

    def transform(self, value):
        """
        Verify value type and permission protocol.
        """
        if not (isinstance(value, list)):
            raise TypeError("field [{}] requires list".format(self.key))
        for p in value:
            passed = False
            for t in PROTO:
                if re.match(t, p) is not None:
                    passed = True
                    break
            if not passed:
                raise TypeError("invalid permission protocol [{}]".format(p))
        return value


class PasswordField(Field):
    """
    This class handles the role password field.
    """

    def __init__(self, key, **kwargs):
        super().__init__(key, **kwargs)
        password_hash = kwargs.get("password_hash")
        if password_hash:
            self.__dict__["value"] = password_hash

    def transform(self, value):
        """
        Verify value type and return a password hash using
        :mod:`werkzeug.security`
        :meth:`generate_password_hash()<werkzeug.security.generate_password_hash>`.
        """
        if value is not None:
            if not isinstance(value, str):
                raise TypeError("field [{}] requires str".format(self.key))
        else:
            return None
        return generate_password_hash(value)

    def verify_password(self, password):
        """
        Verify the password (clear-text) password against the defined password
        hash value.

        :return: ``True`` if the passed password is correct, else ``False``
        """
        return check_password_hash(self.value, password)


class QuotaField(Field):
    """
    This class handles the role rate limit. The quota is defined with two
    integer values seperated by a colon. The first value represents the rate
    limit, the second value represents the number of seconds. For example the
    value ``120:60`` defines a rate limit of 120 requests per minute.
    """

    default = None

    def transform(self, value):
        """
        Verify value type and rate limit definition with ``limit:seconds``.
        """
        if value:
            quota = self._split(value)
            self.limit = quota["limit"]
            self.seconds = quota["seconds"]
        return value

    def _split(self, value):
        """
        Internal method to split the limit definition with ``limit:seconds``.
        """
        match = LIMIT.match(value)
        if match is None:
            raise TypeError(
                "invalid quota protocol [{}], "
                "expected 'limit/seconds'".format(value))
        (limit, seconds) = match.groups()
        return {
            "timestamp": None,
            "seconds": int(seconds),
            "limit": int(limit),
            "current": int(limit)
        }

    def insert(self, collection, _id):
        """
        This method saves the defined rate limit in collection ``sys.quota``.
        """
        if self.value:
            collection.delete_many({"_id": _id})
            quota = self._split(self.value)
            quota["_id"] = _id
            collection.insert_one(quota)
