"""
General purpose helper methods related to node information like hostname,
username, clock and process identifier (PID).
"""
import getpass
import os

import datetime
import socket


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
