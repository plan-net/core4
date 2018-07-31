# -*- coding: utf-8 -*-


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
    """


class Core4RoleNotFound(Core4Error):
    """"
    """


