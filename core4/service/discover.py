import psutil
import socket

import core4.base
import core4.util
from core4.util import lazyproperty


class CoreDiscovery(core4.base.CoreBase):

    @lazyproperty
    def ip_address(self):
        return socket.gethostbyname(core4.util.get_hostname())

    @lazyproperty
    def hostname(self):
        return core4.util.get_hostname()

    @lazyproperty
    def cpu_count(self):
        return psutil.cpu_count(logical=False)

    @lazyproperty
    def mountpoints(self):
        return [d.mountpoint for d in psutil.disk_partitions(all=False)]

    def get_disk_usage(self):
        now = core4.util.now()
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
        now = core4.util.now()
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
            "timestamp": core4.util.now(),
            "total": memory.total,
            "available": memory.available,
            "used": memory.total - memory.available,
            "percent": memory.percent / 100.
        }
