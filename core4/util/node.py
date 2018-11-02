import datetime
import getpass
import os

import socket
# todo: needs to be modified
from flask_login import current_user


def get_hostname():
    """
    :return: hostname
    """
    return socket.gethostname()


def get_username():
    """
    :return: current login's user name
    """
    if 'SUDO_USER' in os.environ:
        return os.environ['SUDO_USER']
    if current_user and hasattr(current_user, 'username'):
        return current_user.username
    return getpass.getuser()


def now():
    """
    :return: current core4 system time (in UTC)
    """
    return datetime.datetime.utcnow()


def mongo_now():
    """
    :return: current core4 system time in MongoDB resolution (in UTC)
    """
    return now().replace(microsecond=0)


def get_pid():
    """
    :return: pid of the current process.
    """
    return os.getpid()