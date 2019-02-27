#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
This module delivers the :class:`.CoreRole` field types.
"""

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
    """
    The base class of all :class:`.CoreRole` attributes. Field objects support
    value getting and setting, validation, and MongoDB document as well as
    HTTP request response features.
    """
    default = None
    field_type = None

    def __init__(self, key, required=False, **kwargs):
        self.initialise()
        self.key = key
        self.required = required
        self.set(kwargs.get(self.key, self.default))

    def initialise(self):
        """
        use to initialise the field object
        """
        pass

    def set(self, value):
        """
        use to set the field value

        :param value: to set
        """
        self.__dict__["value"] = value

    def __setattr__(self, key, value):
        if key == "value":
            self.set(value)
            return
        super().__setattr__(key, value)

    def validate_type(self):
        """
        Validates the value type based on
        :attr:`.field_type <Field.field_type>`.

        Raises :class:`TypeError`
        """
        if self.value is None:
            return
        if not isinstance(self.value, self.field_type):
            raise TypeError("field [{}] must by of type [{}]".format(
                self.key, self.field_type.__name__
            ))

    def validate_value(self):
        """
        Validates the value, i.e. if a :attr:`.required`` field is not
        ``None``.

        Raises :class:`AttributeError`
        """
        if self.required:
            if self.value is None:
                raise AttributeError("field [{}] is mandatory".format(
                    self.key))

    def to_doc(self):
        """
        Translates the field value into a valid MongoDB value.

        :return: variant
        """
        return self.value

    def to_response(self):
        """
        Translates the field value into a valid HTTP resposne value.

        :return: variant
        """
        return self.value


class ObjectIdField(Field):
    """
    Handles role ``_id`` and ``etag`` attribute and verifies the
    value is of type :class:`.ObjectId``.
    """
    field_type = ObjectId


class StringField(Field):
    """
    Handles string attributes. Additional attribute properties
    are :attr:`.required` to indicate non-optional fields and :attr:`regex`
    to perform value validation.
    """
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
    """
    Handles bool attributes with default value ``True``.
    """
    default = True
    field_type = bool


class TimestampField(Field):
    """
    Handles :class:`datetime.datetime` attributes.
    """
    field_type = datetime.datetime


class PermField(Field):
    """
    Handles the ``perm`` attribute, a list of strings with the following
    permission protocols:

    * ``cop`` - administrative role
    * ``job://[qual_name]/[xr]`` - job read and execution permission
    * ``api://[qual_name]`` - api access permission
    * ``app://[key]`` - app key permission
    * ``mongodb://[database]`` - MongoDB database access permission (read-only)

    Raises :class:`AttributeError` if the permission protocol is not valid.
    """
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
    """
    Handles the password field. The class uses :mod:`core4.util.crypt`
    functions to create an assymetric hash value.
    """
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
    """
    Handles the role attribute of a :class:`.CoreRole` object. The role
    attribute stores the list of role names in :attr:`.name` and the role ids
    in :attr:`._id`.
    """
    field_type = list

    def initialise(self):
        self.name = []
        self._id = []
        self.default = []

    def to_response(self):
        return self.name

    def to_doc(self):
        return self._id
