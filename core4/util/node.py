#This Source Code Form is subject to the terms of the Mozilla Public
#License, v. 2.0. If a copy of the MPL was not distributed with this
#file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
General purpose helper methods related to node information like hostname,
username, clock and process identifier (PID).
"""
import getpass
import grp
import os
import pwd

import datetime
import psutil
import socket
import time


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


def get_groups():
    """
    :return: list of group of the current login's user name
    """
    user = get_username()
    groups = [g.gr_name for g in grp.getgrall() if user in g.gr_mem]
    gid = pwd.getpwnam(user).pw_gid
    groups.append(grp.getgrgid(gid).gr_name)
    return groups


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


def uptime():
    """
    :return: node's uptime in :class:`datetime.timedelta`
    """
    return datetime.timedelta(
        seconds=time.time() - psutil.boot_time()
    )
