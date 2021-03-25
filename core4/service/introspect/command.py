#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

#: command used to call :meth:`.CoreIntrospector.run` method
ITERATE = """
from core4.service.introspect.main import CoreIntrospector
print(CoreIntrospector().run(dump=True))
"""

#: command used to enqueue a job without job arguments
ENQUEUE = """
from core4.queue.main import CoreQueue
queue = CoreQueue()
job = queue.enqueue("{qual_name:s}")
print(job._id)
"""

#: command used to enqueue a job including job arguments
ENQUEUE_ARG = """
from core4.queue.main import CoreQueue
queue = CoreQueue()
job = queue.enqueue("{qual_name:s}", {args:s})
if job:
    print(job._id)
"""

#: command used to start job processing with :meth:`.CoreWorkerProecess.start`
EXECUTE = """
import signal
signal.signal(signal.SIGCHLD, signal.SIG_DFL)
from core4.queue.process import CoreWorkerProcess
CoreWorkerProcess().start("{job_id:s}")
"""

#: command used to kill a job with :meth:`.CoreQueue._exec_kill`
KILL = """
from core4.queue.main import CoreQueue
from bson.objectid import ObjectId
CoreQueue().kill_job(ObjectId("{job_id:s}"))
"""

#: command used to restart a job with :meth:`.CoreQueue._exec_restart`
RESTART = """
from core4.queue.main import CoreQueue
from bson.objectid import ObjectId
print(CoreQueue().restart_job(ObjectId("{job_id:s}")))
"""

#: command used to launch selected app servers in project
SERVE = """
from core4.api.v1.tool.functool import serve
from core4.logger.mixin import logon
logon()
serve(*{a}, core4api=False, **{kw})
"""

#: command used to remove a job with :meth:`.CoreQueue.remove_job`
REMOVE = """
from core4.queue.main import CoreQueue
from bson.objectid import ObjectId
print(CoreQueue().remove_job(ObjectId("{job_id:s}")))
"""
