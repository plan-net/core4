import re

import datetime
from bson.objectid import ObjectId

import core4.util.crypt
from core4.const import COP

PROTOCOL = [
    re.compile(r"^" + COP + "$"),
    re.compile(r"^job://[^\s\/]+/[xr]$"),
    re.compile(r"^api://[^\s\/]+$"),
    re.compile(r"^app://[^\s]+$"),
    re.compile(r"^mongodb://[^\s]+$")
]
JOB_EXECUTION_RIGHT = 'x'
JOB_READ_RIGHT = 'r'


class Field:
    default = None
    field_type = None

    def __init__(self, key, required=False, **kwargs):
        self.initialise()
        self.key = key
        self.required = required
        self.set(kwargs.get(self.key, self.default))

    def initialise(self):
        pass

    def set(self, value):
        self.__dict__["value"] = value

    def __setattr__(self, key, value):
        if key == "value":
            self.set(value)
            return
        super().__setattr__(key, value)

    def validate_type(self):
        if self.value is None:
            return
        if not isinstance(self.value, self.field_type):
            raise TypeError("field [{}] must by of type [{}]".format(
                self.key, self.field_type.__name__
            ))

    def validate_value(self):
        if self.required:
            if self.value is None:
                raise AttributeError("field [{}] is mandatory".format(
                    self.key))

    def to_mongo(self):
        return self.value

    def to_response(self):
        return self.value


class ObjectIdField(Field):
    field_type = ObjectId


class StringField(Field):
    field_type = str

    def __init__(self, *args, regex=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.regex = regex

    def validate_value(self):
        if self.required:
            if self.value is None or self.value.strip() == "":
                raise AttributeError("field [{}] is mandatory".format(
                    self.key))
        if self.value is not None:
            self.value = self.value.strip()
            if self.regex is not None:
                if not self.regex.match(self.value) is not None:
                    raise TypeError("field [{}] must match [{}]".format(
                        self.key, self.regex.pattern))
        return True


class BoolField(Field):
    default = True
    field_type = bool


class TimestampField(Field):
    field_type = datetime.datetime


class PermField(Field):
    field_type = list

    def initialise(self):
        self.default = []

    def validate_value(self):
        super().validate_value()
        for actual in self.value:
            passed = False
            for expected in PROTOCOL:
                if re.match(expected, actual) is not None:
                    passed = True
                    break
            if not passed:
                raise AttributeError(
                    "invalid permission protocol [{}]".format(actual))


class PasswordField(Field):
    field_type = str

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set(self, value):
        if value is not None:
            value = core4.util.crypt.pwd_context.hash(value)
        else:
            value = value
        super().set(value)


class RoleField(Field):
    field_type = list

    def initialise(self):
        self.name = []
        self._id = []
        self.default = []

    def to_response(self):
        return self.name

    def to_mongo(self):
        return self._id


