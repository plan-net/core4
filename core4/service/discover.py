#
#Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
#This Source Code Form is subject to the terms of the Mozilla Public
#License, v. 2.0. If a copy of the MPL was not distributed with this
#file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Implements :class:`.CoreDiscovery` for node discovery.
"""
import psutil
import socket

import core4.base
import core4.util.node
from core4.util.tool import lazyproperty


class CoreDiscovery(core4.base.CoreBase):
    """
    Provides general purpose node information, i.e.

    * ip address
    * hostname
    * number of cpu
    * mountpoins
    * current disk usage
    * current cpu usage
    * current memory usage
    """

    @lazyproperty
    def ip_address(self):
        return socket.gethostbyname(core4.util.node.get_hostname())

    @lazyproperty
    def hostname(self):
        return core4.util.node.get_hostname()

    @lazyproperty
    def cpu_count(self):
        return psutil.cpu_count(logical=False)

    @lazyproperty
    def mountpoints(self):
        return [d.mountpoint for d in psutil.disk_partitions(all=False)]

    def get_disk_usage(self):
        now = core4.util.node.now()
        for mp in self.mountpoints:
            du = psutil.disk_usage(mp)
            if du.total > 0:
                yield {
                    "path": mp,
                    "timestamp": now,
                    "total": du.total,
                    "free": du.free,
                    "percent": du.percent / 100.
                }

    def get_cpu_usage(self):
        now = core4.util.node.now()
        for (n, cpu) in enumerate(psutil.cpu_times_percent(percpu=True)):
            yield {
                "cpu": n,
                "timestamp": now,
                "system": cpu.system,
                "user": cpu.user,
                "idle": cpu.idle,
                "iowait": cpu.iowait
            }

    def get_memory_usage(self):
        memory = psutil.virtual_memory()
        return {
            "timestamp": core4.util.node.now(),
            "total": memory.total,
            "available": memory.available,
            "used": memory.total - memory.available,
            "percent": memory.percent / 100.
        }
