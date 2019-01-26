ITERATE = """
from core4.service.introspect import CoreIntrospector
print(CoreIntrospector().iter_all())
"""

ENQUEUE = """
from core4.queue.main import CoreQueue
queue = CoreQueue()
job = queue.enqueue("{qual_name:s}")
print(job._id)
"""

ENQUEUE_ARG = """
from core4.queue.main import CoreQueue
queue = CoreQueue()
job = queue.enqueue("{qual_name:s}", {args:s})
print(job._id)
"""

EXECUTE = """
from core4.queue.process import CoreWorkerProcess
CoreWorkerProcess().start("{job_id:s}")
"""

KILL = """
from core4.queue.main import CoreQueue
CoreQueue()._exec_kill("{job_id:s}")
"""

RESTART = """
from core4.queue.main import CoreQueue
CoreQueue()._exec_restart("{job_id:s}")
"""
