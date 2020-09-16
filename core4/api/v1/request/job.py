import os
import re
import sys

from bson.objectid import ObjectId
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
                     rec["fullDocument"]["message"])
    if match:
        if match.groups()[0] in STATE_FINAL:
            return True
    return False


class JobRequest(CoreRequestHandler):
    """
    core4 job management request to

    * enqueue jobs
    * retrieve queue listing
    * retrieve job details
    * kill jobs (``PUT /job/kill/:id``)
    * remove jobs (``PUT /job/remove/:id``)
    * restart jobs (``PUT /job/restart/:id``)
    * get available jobs (``GET /job/list``)
    * follow jobs (``GET /job/follow``)
    * read job logs (``GET /job/log``)
    """

    author = "mra"
    title = "job management"
    tag = "api jobs"

    @property
    def queue(self):
        self._queue = getattr(self, "_queue", None) or \
                      core4.queue.main.CoreQueue()
        return self._queue

    async def post(self, args=None):
        """
        enqueue new job and retrieve current job list

        Methods:
            POST /core4/api/v1/job - enqueue new job and receive SSE state/log stream

        Parameters:
            qual_name (str)
            follow (bool) - receive state/log stream (True) or job id (False)
            args (dict) - job arguments

        Returns:
            SSE event stream with type ``state`` delivering the job document
            from ``sys.queue`` and type ``log`` delivering the jog log from
            ``sys.log``. If ``follow is False`` then the response body delivers
            the created ``job_id``.

        Raises:
            401 Unauthorized:
            403 Forbidden
            404 Not Found
            500 Server Error (failed to enqueue)

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
            page (int)
            per_page (int)
            filter (dict) - MongoDB json query
            sort (list) - list of 2-element list with key and direction

        Returns:
            paginated list of job details from ``sys.queue``. Note that jobs
            without access permissions are masked with ``UnauthorizedJob``.

        Raises:
            401 Unauthorized:
            403 Forbidden

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
        get current job list, job details, follow running jobs states  and job
        logging

        Methods:
            GET /core4/api/v1/job - retrieve current jobs list

        see :meth:`.post` (``POST /core4/api/v1/job``)

        Methods:
            GET /core4/api/v1/job/<_id> - retrieve job details

        Parameters:
            _id (ObjectId) - job _id

        Returns:
            Job details retrieved from ``sys.queue`` for current jobs and from
            ``sys.journal`` for past jobs

        Raises:
            401 Unauthorized:
            403 Forbidden

        Examples:
            >>> from requests import get
            >>> rv = get("http://localhost:5001/core4/api/v1/job/5f62217f4f5b043ae1b00a05",
            ...          auth=("admin", "hans"))
            >>> rv
            <Response [200]>

        Methods:
            GET /core4/api/v1/job/follow/<_id> - follow running job

        Parameters:
            _id (ObjectId)

        Returns:
            SSE event stream with type ``state`` delivering the job document
            from ``sys.queue`` and type ``log`` delivering the jog log from
            ``sys.log``.

        Raises:
            401 Unauthorized:
            403 Forbidden

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
            _id (ObjectId) - job _id
            follow (bool) - ``True`` for SSE streaming, ``False`` for paginated
            log retrieval

        Returns:
            SSE event stream with type ``log`` delivering the jog log from
            ``sys.log``.

        Raises:
            401 Unauthorized:
            403 Forbidden

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
            page (int)
            per_page (int)
            filter (dict) - MongoDB json query
            sort (list) - list of 2-element list with key and direction
            search (str) - free text search in ``qual_name``

        Returns:
            list of jobs with ``qual_name`` (``_id``), ``author``,
            ``create_at``, ``doc`` (docstring), ``schedule``, ``tag`` and
            ``updated_at``

        Raises:
            401 Unauthorized:

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
            action (str) - any of ``kill``, ``restart``, or ``remove``
                _id (ObjectId) - job _id
            follow (bool) - follow the restarted job (defaults to ``True``).
                This option applies only to the ``restart`` action.

        Returns:
            True

        Raises:
            401 Unauthorized:
            403 Forbidden
            404 Not Found

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
        oid = ObjectId(_id)
        self.logger.info("following [%s]", _id)
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
            pipeline=[{
                "$match": {
                    "operationType": "insert",
                    "fullDocument.identifier": str(_id)
                }
            }])
        # verify the job exists
        follow = await self.config.sys.queue.count_documents({"_id": oid}) > 0
        done = False
        # get old logs
        doc = await self.config.sys.log.find_one(
            {"identifier": _id}, sort=[("_id", 1)])
        if doc:
            first_log = doc["_id"]
        else:
            first_log = None

        async def _pre_log(rec=None):
            """
            helper method to query job logs materialised before streaming starts
            """
            nonlocal first_log
            if first_log is None:
                return True
            first_log = None
            query = {"identifier": _id}
            if rec:
                query["_id"] = {"$lt": rec["_id"]}
            cur = self.config.sys.log.find(query, sort=[("_id", 1)])
            for doc in await cur.to_list(None):
                if not await self.sse("log", doc):
                    return False
            return True

        self.logger.info("stream open")
        # follow sys.queue and sys.log
        while follow:
            job_change = await job_stream.try_next()
            log_change = await log_stream.try_next()
            if job_change:
                ops = job_change.get("operationType", None)
                doc = job_change.get('fullDocument', {})
                if ops:
                    if ops == "delete":
                        follow = False
                    if doc:
                        state = doc["state"]
                        if follow_state:
                            if (not await self.sse("state", doc) or
                                    (state in STATE_FINAL)):
                                follow = False
            if log_change:
                if end_of_job(log_change):
                    done = True
                log_change["fullDocument"]["postproc"] = False
                if not await _pre_log(log_change["fullDocument"]):
                    follow = False
                if not await self.sse("log", log_change["fullDocument"]):
                    follow = False
        # process not yet received logs
        t0 = core4.util.node.now()
        while not done:
            log_change = await log_stream.try_next()
            if log_change:
                if end_of_job(log_change):
                    done = True
                log_change["fullDocument"]["postproc"] = True
                if not await _pre_log(log_change["fullDocument"]):
                    break
                if not await self.sse("log", log_change["fullDocument"]):
                    break
            if (core4.util.node.now() - t0).total_seconds() > FOLLOW_WAIT:
                break
        await _pre_log()
        await log_stream.close()
        await job_stream.close()
        await self.sse("close", {})
        self.logger.info("stream close by server")
        self.finish()

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
        except StreamClosedError:
            self.logger.info("stream close by client")
            return False
        except Exception:
            self.logger.error("stream error", exc_info=True)
            return False
        return True

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
                ".", "\.").replace(
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
