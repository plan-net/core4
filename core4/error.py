#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Implements all core4 specific exceptions
"""

from tornado.web import HTTPError


class Core4Error(Exception):
    """
    This is the base class of all core4 exceptions.
    """


class Core4SetupError(Core4Error):
    """
    This exception is raised if core4 is not properly configured. Further
    details are available in the exception message.
    """


class Core4ConfigurationError(Core4Error):
    """"
    This exception is raised if core4 configuration cannot be parsed. Further
    details are available in the exception message.
    """


class Core4ConflictError(Core4Error):
    """"
    This exception is raised if core4 encounters an update conflict, i.e. if
    the etag does not match current document status.
    """


class Core4RoleNotFound(Core4Error):
    """"
    This exception is raised if a role/user does not exist.
    """


class Core4UsageError(Core4Error):
    """"
    This exception is raised if the application or usage or a core4 class
    feature is not supported.
    """


class CoreJobDeferred(Core4Error):
    """"
    This exception is raised if a job defers execution.
    """


class CoreJobNotFound(Core4Error):
    """
    This exception is raised if the job is not found.
    """


class CoreJobExists(Core4Error):
    """
    This exception is raised if the job already exists as defined by the
    name/qual_name and job arguments.
    """

class ArgumentParsingError(HTTPError):
    """
    This exception is raised if an error occured while parsing query or body
    parameters in the context of core API.
    """
    def __init__(self, log_message=None, *args, status_code=400, **kwargs):
        super().__init__(status_code, log_message, *args, **kwargs)
