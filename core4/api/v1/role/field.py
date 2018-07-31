# -*- coding: utf-8 -*-

import re

import datetime
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

import core4.util

COP = "cop"
PROTO = [
    re.compile("^" + COP + "$"),
    re.compile("^job://[^\s\/]+/[xr]$"),
    re.compile("^api://[^\s\/]+$"),
    re.compile("^app://[^\s]+$"),
    re.compile("^mongodb://[^\s]+$")
]

JOB_EXECUTION_RIGHT = 'x'
JOB_READ_RIGHT = 'r'


class Field:
    default = None

    def __init__(self, key, **kwargs):
        super().__init__()
        self.key = key
        self.value = kwargs.get(self.key, self.default)

    def validate(self):
        return True

    def transform(self, value):
        raise NotImplementedError()  # pragma: no cover

    def to_mongo(self):
        return self.value

    def __setattr__(self, key, value):
        if key == "value":
            value = self.transform(value)
        super().__setattr__(key, value)


class ObjectIdField(Field):

    def transform(self, value):
        if not (value is None or isinstance(value, ObjectId)):
            raise TypeError("field [{}] requires ObjectId".format(self.key))
        return value


class StringField(Field):

    def __init__(self, key, required=False, regex=None, **kwargs):
        self.required = required
        self.regex = regex
        super().__init__(key, **kwargs)

    def validate(self):
        if self.required:
            if self.value is None or self.value.strip() == "":
                raise TypeError("field [{}] is mandatory".format(self.key))
        return True

    def transform(self, value):
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
    default = True

    def transform(self, value):
        if not (isinstance(value, bool)):
            raise TypeError("field [{}] requires bool".format(self.key))
        return value

class TimestampField(Field):

    def transform(self, value):
        if not (value is None
                or isinstance(value, datetime.datetime)):
            raise TypeError("field [{}] requires datetime".format(self.key))
        return value

    def update(self):
        self.value = core4.util.now()


class PermField(Field):
    default = []

    def transform(self, value):
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


class TokenField(Field):
    pass


class PasswordField(Field):
    def __init__(self, key, **kwargs):
        super().__init__(key, **kwargs)
        password_hash = kwargs.get("password_hash")
        if password_hash:
            self.__dict__["value"] = password_hash

    def transform(self, value):
        if value is not None:
            if not isinstance(value, str):
                raise TypeError("field [{}] requires str".format(self.key))
        else:
            return None
        return generate_password_hash(value)

    # def to_mongo(self):
    #     if self.value is not None:
    #         self.password_hash = generate_password_hash(self.value)
    #         return self.password_hash

    def verify_password(self, password):
        return check_password_hash(self.value, password)


class LimitField(Field):
    pass
