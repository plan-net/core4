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
