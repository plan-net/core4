#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import re
import sys
from datetime import timedelta

import tornado.gen
from bson.objectid import ObjectId
from tornado.ioloop import IOLoop
from tornado.iostream import StreamClosedError
from tornado.process import Subprocess
from tornado.web import HTTPError

import core4.const
import core4.queue.job
import core4.queue.main
import core4.util.data
import core4.util.node
from core4.api.v1.request.main import CoreRequestHandler
from core4.service.introspect.command import KILL, REMOVE, RESTART, ENQUEUE_ARG
from core4.util.pager import CorePager

STATE_STOPPED = (
    core4.queue.job.STATE_KILLED,
    core4.queue.job.STATE_INACTIVE,
    core4.queue.job.STATE_ERROR)
STATE_FINAL = (
    core4.queue.job.STATE_COMPLETE,
    *STATE_STOPPED
)
STATE_WAITING = (
    core4.queue.job.STATE_DEFERRED,
    core4.queue.job.STATE_FAILED,
    core4.queue.job.STATE_PENDING)

FOLLOW_WAIT = 3.
FRIENDLY_COUNT = 1000


class JobError(HTTPError):
    default_status = 500

    def __init__(self, log_message=None, *args, **kwargs):
        super().__init__(self.default_status, log_message, *args, **kwargs)


class JobNotFound(JobError):
    default_status = 404


class JobExists(JobError):
    default_status = 400


class JobArgumentError(JobError):
    default_status = 400


class JobUnauthorized(JobError):
    default_status = 403


ACTION = {
    "enqueue": ENQUEUE_ARG,
    "kill": KILL,
    "restart": RESTART,
    "remove": REMOVE
}


def enrich_job(doc):
    """
    Helper method to enrich job properties from ``sys.queue``. The following
    properties are added:

    * ``highstate`` with *running*, *stopped* (_killed_, _inactive_ and
      _error_), *waiting* (_deferred_, _failed_ and _pending_)
    * ``flag`` with _zombie_, _killed_, _removed_ and _nonstop_
    * ``age`` from _enqueued.at_ to _now_

    :param doc: MongoDB document
    :return: enriched document
    """
    doc["highstate"] = None
    for k, v in (("waiting", STATE_WAITING),
                 ("stopped", STATE_STOPPED),
                 ("running", (core4.queue.job.STATE_RUNNING))):
        if doc["state"] in v:
            doc["highstate"] = k
            break
    doc["prog"]["value"] = doc["prog"]["value"] or 0.
    doc["flag"] = {
        "zombie": doc["zombie_at"] is not None,
        "killed": doc["killed_at"] is not None,
        "removed": doc["removed_at"] is not None,
        "nonstop": doc["wall_at"] is not None
    }
    doc["age"] = (core4.util.node.now()
                  - doc["enqueued"]["at"]).total_seconds()
    doc["qual_name"] = doc["name"]
    del doc["name"]
    return doc


def end_of_job(rec):
    """
    Helper method to indentify job completion from ``sys.log``.
    """
    match = re.match(r"done execution with \[(.+?)\]",
                     rec["message"])
    if match:
        if match.groups()[0] in STATE_FINAL:
            return True
    return False


class JobRequest(CoreRequestHandler):
    """
    Job Management Handler delivers

    * listing of available jobs
    * enqueuing of jobs
    * streaming job states, progress and logging
    * retrieve running jobs
    * retrieve details of current and past jobs
    * kill, restart and remove jobs
    """

    title = "Job Management"
    subtitle = "Enqueue and Manage Jobs"
    tag = "api jobs"
    doc = "Job Management Handler"

    def initialise_object(self):
        super().initialise_object()
        self._stop_state = False
        self._stop_log = False
        self._last_log = None
        self._count = {}
        self._friendly = FRIENDLY_COUNT

    @property
    def queue(self):
        self._queue = getattr(self, "_queue", None) or \
                      core4.queue.main.CoreQueue()
        return self._queue

    async def post(self, args=None):
        """
        enqueue new job and retrieve current job list

        Methods:
            POST /core4/api/v1/job - enqueue new job and receive state stream

        Parameters:
            - qual_name (str)
            - follow (bool): receive state/log stream (True) or job id (False)
            - args (dict): job arguments

        Returns:
            SSE event stream with type ``state`` delivering the job document
            from ``sys.queue`` and type ``log`` delivering the jog log from
            ``sys.log``. If ``follow is False`` then the response body delivers
            the created ``job_id``.

        Raises:
            401: Unauthorized
            403: Forbidden
            404: Not Found
            500: Server Error (failed to enqueue)

        Examples:
            >>> from requests import post
            >>> rv = post("http://localhost:5001/core4/api/v1/job",
            ...           json={
            ...               "qual_name": "core4.queue.helper.job.example.DummyJob",
            ...               "args": {"sleep": 15},
            ...               "follow": False
            ...           }, auth=("admin", "hans"))
            ...
            >>> rv
            <Response [200]>

        Methods:
            POST /core4/api/v1/job/queue - retrieve current jobs list

        Parameters:
            - page (int)
            - per_page (int)
            - filter (dict): MongoDB json query
            - sort (list): list of 2-element list with key and direction

        Returns:
            paginated list of job details from ``sys.queue``. Note that jobs
            without access permissions are masked with ``UnauthorizedJob``.

        Raises:
            401: Unauthorized:
            403: Forbidden

        Examples:
            >>> from requests import post
            >>> rv = post("http://localhost:5001/core4/api/v1/job/queue",
            ...           auth=("admin", "hans"))
            >>> rv
            <Response [200]>
        """
        if args:
            return await self.dispatch("post", args)
        else:
            await self._post_enqueue()

    async def get(self, args=None):
        """
        get current job list, job details, follow running jobs states and job
        logging

        Methods:
            GET /core4/api/v1/job - see :meth:`.post`

        Methods:
            GET /core4/api/v1/job/<_id> - retrieve job details

        Parameters:
            - _id (ObjectId): job _id

        Returns:
            Job details retrieved from ``sys.queue`` for current jobs and from
            ``sys.journal`` for past jobs

        Raises:
            401: Unauthorized
            403: Forbidden

        Examples:
            >>> from requests import get
            >>> rv = get("http://localhost:5001/core4/api/v1/job/5f62217f4f5b043ae1b00a05",
            ...          auth=("admin", "hans"))
            >>> rv
            <Response [200]>

        Methods:
            GET /core4/api/v1/job/follow/<_id> - follow active job

        Parameters:
            - _id (ObjectId)

        Returns:
            SSE event stream with type ``state`` delivering the job document
            from ``sys.queue`` and type ``log`` delivering the jog log from
            ``sys.log``.

        Raises:
            401: Unauthorized:
            403: Forbidden

        Examples:
            >>> from requests import post, get
            >>> rv = post("http://localhost:5001/core4/api/v1/job",
            ...           json={
            ...               "qual_name": "core4.queue.helper.job.example.DummyJob",
            ...               "args": {"sleep": 120},
            ...               "follow": False
            ...           }, auth=("admin", "hans"))
            ...
            >>> rv
            <Response [200]>
            >>> jid = rv.json()["data"]
            >>> rv = get("http://localhost:5001/core4/api/v1/job/follow/" + jid,
            ...           auth=("admin", "hans"), stream=True)
            >>> for line in rv:
            ...     print(line)

        Methods:
            GET /core4/api/v1/job/log/<_id> - follow job log

        Parameters:
            - _id (ObjectId): job _id
            - follow (bool): ``True`` for SSE streaming, ``False`` for
              paginated log retrieval

        Returns:
            SSE event stream with type ``log`` delivering the jog log from
            ``sys.log``.

        Raises:
            401: Unauthorized:
            403: Forbidden

        Examples:
            >>> from requests import post, get
            >>> rv = post("http://localhost:5001/core4/api/v1/job",
            ...           json={
            ...               "qual_name": "core4.queue.helper.job.example.DummyJob",
            ...               "args": {"sleep": 120},
            ...               "follow": False
            ...           }, auth=("admin", "hans"))
            ...
            >>> rv
            <Response [200]>
            >>> jid = rv.json()["data"]
            >>> rv = get("http://localhost:5001/core4/api/v1/job/log/" + jid,
            ...           auth=("admin", "hans"), stream=True)
            >>> for line in rv:
            ...     print(line)

        Methods:
            GET /core4/api/v1/job/list - retrieve paginated list of jobs

        Parameters:
            - page (int)
            - per_page (int)
            - filter (dict): MongoDB json query
            - sort (list): list of 2-element list with key and direction
            - search (str): free text search in ``qual_name``

        Returns:
            list of jobs with ``qual_name`` (``_id``), ``author``,
            ``create_at``, ``doc`` (docstring), ``schedule``, ``tag`` and
            ``updated_at``

        Raises:
            401: Unauthorized

        Examples:
            >>> from requests import get
            >>> rv = get("http://localhost:5001/core4/api/v1/job/list",
            ...          auth=("admin", "hans"))
            ...
            >>> rv
            <Response [200]>
        """
        if args:
            parts = args.split("/")
            if parts:
                try:
                    _ = ObjectId(parts[0])
                except:
                    pass
                else:
                    return await self._get_detail(parts[0])
            return await self.dispatch("get", args)
        else:
            await self._get_queue()

    async def put(self, args):
        """
        handle jobs, i.e. kill, restart and remove

        Methods:
            PUT /core4/api/v1/job/<action>/<_id> - act on a job

        Parameters:
            - action (str): any of ``kill``, ``restart``, or ``remove``
            - _id (ObjectId): job _id
            - follow (bool): follow the restarted job (defaults to ``True``).
              This option applies only to the ``restart`` action.

        Returns:
            True

        Raises:
            401: Unauthorized:
            403: Forbidden
            404: Not Found

        Examples:
            >>> from requests import get
            >>> rv = put("http://localhost:5001/core4/api/v1/job/remove/5f62217f4f5b043ae1b00a05",
            ...          auth=("admin", "hans"))
            >>> rv
            <Response [200]>
        """
        return await self.dispatch("put", args)

    async def dispatch(self, method, args):
        """
        helper method to dispatch requests to the method
        """
        (action, *param) = args.split("/")
        meth = getattr(self, "_" + method + "_" + action, None)
        if meth is None:
            raise HTTPError(405, "unknown action {} [{}]".format(
                method.upper(), action))
        self.logger.debug("action [%s]", action)
        return await meth(*param)

    async def _post_enqueue(self):
        """
        helper method to enqueue jobs
        """
        qual_name = self.get_argument("qual_name", as_type=str)
        follow = self.get_argument("follow", as_type=bool, default=True)
        args = self.get_argument("args", as_type=dict, default={})
        user_info = {"username": self.current_user}
        try:
            _id = self.queue.enqueue(name=qual_name, by=user_info, **args)._id
        except ImportError:
            stdout, stderr = await self.exec_project(
                "enqueue", qual_name=qual_name, by=user_info, wait=False,
                args="**%s" % (str(args)))
            check = "core4.error.CoreJobExists: job [{}]".format(qual_name)
            if stderr:
                if check in stderr:
                    raise JobExists("job [{}] exists with args {}".format(
                        qual_name, args))
                elif "ImportError: No module" in stderr:
                    raise JobNotFound(qual_name)
                else:
                    error = stderr.strip().split("\n")[-1]
                    raise JobError("failed to enqueue {}: {}".format(
                        qual_name, error))
            _id = ObjectId(stdout)
        if follow:
            await self._get_follow(_id)
        else:
            self.logger.info("enqueued [%s] with _id [%s]", qual_name, _id)
            self.reply(_id)

    async def _post_queue(self):
        """
        helper method to list the queue with POST
        """
        return await self._get_queue()

    async def _get_queue(self):
        """
        helper method to list the queue with GET
        """

        async def _length(filter):
            return await self.config.sys.queue.count_documents(filter)

        async def _query(skip, limit, filter, sort_by):
            projection = {
                "_id": 1,
                "started_at": 1,
                "finished_at": 1,
                "runtime": 1,
                "force": 1,
                "name": 1,
                "worker": 1,
                "attempts_left": 1,
                "enqueued": 1,
                "priority": 1,
                "state": 1,
                "trial": 1,
                "prog": 1,
                "args": 1,
                "attempts": 1,
                "inactive_at": 1,
                "zombie_at": 1,
                "killed_at": 1,
                "removed_at": 1,
                "wall_at": 1,
            }
            cur = self.config.sys.queue.find(
                filter, projection).skip(skip).sort(sort_by).limit(limit)
            data = []
            perm_cache = {}
            for doc in await cur.to_list(limit):
                doc = enrich_job(doc)
                if doc["qual_name"] not in perm_cache:
                    grant = await self.user.has_job_access(doc["qual_name"])
                    perm_cache[doc["qual_name"]] = grant
                if not perm_cache[doc["qual_name"]]:
                    doc["qual_name"] = "UnauthorizedJob"
                    doc["args"] = None
                data.append(doc)
            return data

        per_page = int(
            self.get_argument("per_page", as_type=int, default=10))
        current_page = int(
            self.get_argument("page", as_type=int, default=0))
        query_filter = self.get_argument("filter", as_type=dict, default={})
        sort_by = self.get_argument("sort", as_type=list,
                                    default=[["_id", 1]])
        pager = CorePager(
            per_page=per_page,
            current_page=current_page,
            length=_length,
            query=_query,
            sort_by=sort_by,
            filter=query_filter
        )
        self.reply(await pager.page())

    async def _get_detail(self, *args):
        """
        helper method to retrieve job details from ``sys.queue`` and
        ``sys.journal``
        """
        if not args:
            raise JobArgumentError("missing job _id")
        self.reply(await self.find_job(args[0]))

    async def find_job(self, _id):
        """
        helper method to query a job from ``sys.queue`` or ``sys.journal``
        """
        oid = ObjectId(_id)
        doc = await self.config.sys.queue.find_one({"_id": oid})
        if doc is None:
            doc = await self.config.sys.journal.find_one({"_id": oid})
            if doc is not None:
                doc["journal"] = True
        else:
            doc["journal"] = False
        if doc is None:
            raise JobNotFound(_id)
        doc = enrich_job(doc)
        if not await self.user.has_job_access(doc["qual_name"]):
            raise JobUnauthorized(_id)
        return doc

    async def _get_log(self, *args):
        """
        helper method to follow the job log (streamed or paginated)
        """
        if not args:
            raise JobArgumentError("missing job _id")
        follow = self.get_argument("follow", as_type=bool, default=False)
        # verify access
        await self.find_job(args[0])
        if follow:
            await self._stream_log(args[0], follow_state=False)
        else:
            await self._page_log(args[0])

    async def _page_log(self, _id):
        """
        helper method to follow the job log (paginated)
        """

        async def _length(filter):
            return await self.config.sys.log.count_documents(filter)

        async def _query(skip, limit, filter, sort_by):
            cur = self.config.sys.log.find(filter).skip(skip).sort(
                sort_by).limit(limit)
            return await cur.to_list(limit)

        per_page = int(
            self.get_argument("per_page", as_type=int, default=10))
        current_page = int(
            self.get_argument("page", as_type=int, default=0))
        query_filter = self.get_argument("filter", as_type=dict, default={})
        sort_by = self.get_argument("sort", as_type=list,
                                    default=[["_id", 1]])
        query_filter["identifier"] = str(_id)
        pager = CorePager(
            per_page=per_page,
            current_page=current_page,
            length=_length,
            query=_query,
            sort_by=sort_by,
            filter=query_filter
        )
        self.reply(await pager.page())

    async def _stream_log(self, _id, follow_state=True):
        """
        helper method to follow the job log (streamed)
        """
        self.set_header("Content-Type", "text/event-stream")
        self.set_header("Cache-Control", "no-cache")
        self.set_header("X-Accel-Buffering", "no")
        oid = ObjectId(_id)
        self.logger.info("following job [%s]", _id)

        follow = True
        job_doc = await self.config.sys.queue.find_one({"_id": oid})
        job_stream = None
        log_stream = None
        if job_doc is not None:
            self.logger.debug("job found in sys.queue")
            job_stream = self.config.sys.queue.watch(
                pipeline=[{
                    "$match": {
                        "documentKey._id": oid,
                        "operationType": {
                            "$in": ["update", "delete"]
                        }
                    }
                }], full_document="updateLookup")
            log_stream = self.config.sys.log.watch(
                pipeline=[
                    {"$match": {
                        "operationType": "insert",
                        "fullDocument.identifier": str(_id)
                    }
                    }]
            )
        else:
            self.logger.debug("job found in sys.journal")
            follow = False
            job_doc = await self.config.sys.journal.find_one({"_id": oid})
            if job_doc is None:
                raise HTTPError(404, "job not found")

        try:
            if follow_state:
                await self.sse("state", job_doc)

            query = {"identifier": str(_id)}
            cur = self.config.sys.log.find(query, sort=[("_id", 1)])
            for doc in await cur.to_list(None):
                doc["mode"] = "prelog"
                await self.sse("log", doc)
                self._last_log = doc["_id"]

            if follow:
                IOLoop.current().spawn_callback(self._cb_status, job_stream,
                                                follow_state, oid)
                IOLoop.current().spawn_callback(self._cb_log, log_stream)
                self.logger.debug("starting loop")
                while not (self._stop_state and self._stop_log):
                    await tornado.gen.sleep(0.25)

            if self._last_log is not None:
                query["_id"] = {"$gt": self._last_log}

            cur = self.config.sys.log.find(query, sort=[("_id", 1)])
            for doc in await cur.to_list(None):
                doc["mode"] = "postlog"
                await self.sse("log", doc)

            await self.sse("close", self._count)

        except Exception:
            self.logger.error("error occured", exc_info=True)

        if job_stream is not None:
            await job_stream.close()
        if log_stream is not None:
            await log_stream.close()

        self.logger.info("stream close by server")
        self.finish()

    async def _cb_status(self, stream, follow, oid):
        t0 = None
        while True:
            change = await stream.try_next()
            if change:
                ops = change.get("operationType", None)
                self.logger.debug("operation [%s]", ops)
                if ops:
                    if ops == "delete":
                        break
                    else:
                        upd = change["fullDocument"]
                        state = upd.get("state", None)
                        self.logger.debug("job state [%s]", state)
                        if upd:
                            if follow:
                                await self.sse("state", upd)
                            if state in STATE_FINAL:
                                break
            else:
                if t0:
                    if core4.util.node.now() > t0:
                        job_doc = await self.config.sys.queue.find_one(
                            {"_id": oid})
                        if job_doc is None:
                            self.logger.warning("state query timeout")
                            break
                        else:
                            state = job_doc.get("state", None)
                            self.logger.debug("job state [%s]", state)
                            if state in STATE_FINAL:
                                if follow:
                                    await self.sse("state", job_doc)
                                break
                    else:
                        tornado.gen.sleep(0.25)
                else:
                    t0 = core4.util.node.now() + timedelta(seconds=FOLLOW_WAIT)
        self.logger.debug("exit status stream")
        self._stop_state = True

    async def _cb_log(self, stream):
        t0 = None
        while True:
            change = await stream.try_next()
            if change:
                doc = change["fullDocument"]
                doc["mode"] = "watchlog"
                if self._last_log is None or doc["_id"] > self._last_log:
                    await self.sse("log", doc)
                self._last_log = doc["_id"]
            elif self._stop_state:
                if t0:
                    if core4.util.node.now() > t0:
                        self.logger.debug("log query timeout")
                        break
                    else:
                        tornado.gen.sleep(0.5)
                else:
                    t0 = core4.util.node.now() + timedelta(seconds=FOLLOW_WAIT)
        self.logger.debug("exit log stream at %s", self._last_log)
        self._stop_log = True

    async def _put_kill(self, *args):
        """
        helper method to kill a job
        """
        if not args:
            raise JobArgumentError("missing job _id")
        _id = args[0]
        await self.exec_project("kill", job_id=_id)
        self.reply(True)

    async def _put_remove(self, *args):
        """
        helper method to remove a job
        """
        if not args:
            raise JobArgumentError("missing job _id")
        _id = args[0]
        await self.exec_project("remove", job_id=_id)
        self.reply(True)

    async def _put_restart(self, *args):
        """
        helper method to restart a job
        """
        if not args:
            raise JobArgumentError("missing job _id")
        follow = self.get_argument("follow", as_type=bool, default=True)
        _id = args[0]
        stdout, stderr = await self.exec_project(
            "restart", job_id=_id, wait=False)
        if follow:
            await self._get_follow(stdout.strip())
        else:
            self.reply(stdout)

    async def _get_follow(self, *args):
        """
        helper method to follow a job (streamed)
        """
        if not args:
            raise JobArgumentError("missing job _id")
        # verify access
        await self.find_job(args[0])
        return await self._stream_log(args[0])

    async def sse(self, event, doc):
        """
        helper method to send server-sent-events (SSE)
        """
        js = core4.util.data.json_encode(
            doc, indent=None, separators=(',', ':'))
        try:
            self.write("event: " + event + "\n")
            self.write("data: " + js + "\n\n")
            await self.flush()
            self._count.setdefault(event, 0)
            self._count[event] += 1
        except StreamClosedError:
            self.logger.info("stream close by client")
            raise
        except Exception:
            self.logger.error("stream error", exc_info=True)
            raise
        self._friendly -= 1
        if self._friendly <= 0:
            self._friendly = FRIENDLY_COUNT
            await tornado.gen.sleep(FOLLOW_WAIT)

    async def exec_project(self, command_key, qual_name=None, job_id=None,
                           wait=True, *args, **kwargs):
        """
        helper method to execute core4 commands/methods in a different
        environment
        """
        if job_id:
            doc = await self.config.sys.queue.find_one(
                {"_id": ObjectId(job_id)})
            if doc is None:
                raise JobNotFound(job_id)
            qual_name = doc["name"]
        elif qual_name is None:
            raise RuntimeError("requires qual_name or job_id")
        project = qual_name.split(".")[0]
        if not await self.user.has_job_exec_access(qual_name):
            raise HTTPError(403, "access denied to [{}]".format(qual_name))
        currdir = os.path.abspath(os.curdir)
        if self.queue.config.folder.home is not None:
            python_path = os.path.join(self.queue.config.folder.home, project,
                                       core4.const.VENV_PYTHON)
        else:
            python_path = sys.executable
        self.logger.debug("python found at [%s]", python_path)
        kwargs["job_id"] = job_id
        kwargs["qual_name"] = qual_name
        cmd = ACTION[command_key].format(*args, **kwargs)
        env = os.environ.copy()
        self.logger.debug("execute with [%s] in [%s]:\n%s", python_path,
                          currdir, cmd)
        proc = Subprocess([python_path, "-c", cmd], stdout=Subprocess.STREAM,
                          stderr=Subprocess.STREAM, env=env)
        stdout = bytearray(b"")
        stderr = bytearray(b"")
        for inbound in await proc.stdout.read_until_close():
            stdout.append(inbound)
        for inbound in await proc.stderr.read_until_close():
            stderr.append(inbound)
        if wait:
            await proc.wait_for_exit(raise_error=False)
            retcode = proc.returncode
        else:
            retcode = 0
        out = stdout.decode("utf-8").rstrip()
        err = stderr.decode("utf-8").rstrip()
        os.chdir(currdir)
        if retcode != 0:
            raise JobError("failed to [{}] job [{}] as {}\n{}\n{}".format(
                command_key, qual_name, job_id, err, out))
        return (out, err)

    async def _get_list(self):
        """
        helper method to retrieve existing jobs
        """
        per_page = int(self.get_argument(
            "per_page", as_type=int, default=10))
        current_page = int(self.get_argument(
            "page", as_type=int, default=0))
        query_filter = self.get_argument(
            "filter", as_type=dict, default={})
        sort_order = self.get_argument(
            "sort", as_type=list, default=None)
        search = self.get_argument(
            "search", as_type=str, default=None)
        query_filter["valid"] = True
        if "qual_name" in query_filter:
            query_filter["_id"] = query_filter["qual_name"]
            del query_filter["qual_name"]
        elif search is not None:
            search = search.replace(
                ".", "\\.").replace(
                "?", ".").replace(
                "*", ".*")
            query_filter["_id"] = re.compile(search, re.IGNORECASE)

        if sort_order is None:
            sort_order = [("_id", 1)]
        cur = self.config.sys.job.find(query_filter, projection=[
            "_id", "author", "created_at", "doc", "schedule", "tag",
            "updated_at"]).sort(sort_order)
        data = []
        for doc in await cur.to_list(None):
            if await self.user.has_job_exec_access(doc["_id"]):
                data.append(doc)

        async def _length(*args, **kwargs):
            return len(data)

        async def _query(skip, limit, *args, **kwargs):
            return data[skip:(skip + limit)]

        pager = CorePager(per_page=int(per_page),
                          current_page=int(current_page),
                          length=_length, query=_query,
                          sort_by=sort_order,
                          filter=query_filter)
        ret = await pager.page()
        return self.reply(ret)
