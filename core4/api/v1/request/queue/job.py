#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import sys
import traceback
import pymongo
import pymongo.errors
from bson.objectid import ObjectId
from tornado import gen
from tornado.iostream import StreamClosedError
from tornado.web import HTTPError

import core4.const
import core4.error
import core4.queue.job
import core4.queue.query
import core4.util.node
from core4.api.v1.request.main import CoreRequestHandler
from core4.queue.main import CoreQueue
from core4.util.data import json_encode
from core4.util.pager import CorePager

STATE_FINAL = (
    core4.queue.job.STATE_COMPLETE,
    core4.queue.job.STATE_KILLED,
    core4.queue.job.STATE_INACTIVE,
    core4.queue.job.STATE_ERROR)
STATE_WAITING = (
    core4.queue.job.STATE_DEFERRED,
    core4.queue.job.STATE_FAILED)
STATE_STOPPED = (
    core4.queue.job.STATE_KILLED,
    core4.queue.job.STATE_INACTIVE,
    core4.queue.job.STATE_ERROR)


class JobHandler(CoreRequestHandler, core4.queue.query.QueryMixin):
    """
    Get job listing, job details, kill, delete and restart jobs.
    """

    author = "mra"
    title = "job manager"
    tag = ["job management"]

    def initialize(self):
        self.queue = CoreQueue()
        self._collection = {}

    def collection(self, name):
        """
        Singleton connect and return async MongoDB connection.

        :param name: collection name below ``sys``
        :return: :class:`core4.base.collection.CoreCollection`
        """
        if name not in self._collection:
            self._collection[name] = self.config.sys[name]
        return self._collection[name]

    async def get(self, _id=None):
        """
        Paginated job listing with ``/jobs``,  and single job details with
        ``/jobs/<_id>``. Only jobs with read/execute access permissions granted
        to the current user are returned.

        Methods:
            GET /jobs - jobs listing

        Parameters:
            per_page (int): number of jobs per page
            page (int): requested page (starts counting with ``0``)
            sort (str): sort field
            order (int): sort direction (``1`` for ascending, ``-1`` for
                         descending)

        Returns:
            data element with list of job attributes as dictionaries. For
            pagination the following top level attributes are returned:

            - **total_count**: the total number of records
            - **count**: the number of records in current page
            - **page**: current page (starts counting with ``0``)
            - **page_count**: the total number of pages
            - **per_page**: the number of elements per page

        Raises:
            401: Unauthorized

        Examples:
            >>> from requests import get, post
            >>> from pprint import pprint
            >>> import random
            >>> url = "http://localhost:5001/core4/api/v1"
            >>> signin = get(url + "/login?username=admin&password=hans")
            >>> token = signin.json()["data"]["token"]
            >>> h = {"Authorization": "Bearer " + token}
            >>>
            >>> name = "core4.queue.helper.DummyJob"
            >>> for i in range(50):
            >>>     args = {"sleep": i, "id": random.randint(0, 100)}
            >>>     rv = post(url + "/enqueue?name=" + name, headers=h, json=args)
            >>>     print(i, rv.status_code, "-", rv.json()["message"])
            >>>     assert rv.status_code == 200
            >>> rv = get(url + "/jobs?per_page=10&sort=args.id&order=-1", headers=h)
            >>> rv
            <Response [200]>
            >>> rv.json()
            {
                '_id': '5be13b56de8b69468b7ff0b2',
                'code': 200,
                'message': 'OK',
                'timestamp': '2018-11-06T06:57:26.660093',
                'total_count': 50.0,
                'count': 10,
                'page': 0,
                'page_count': 5,
                'per_page': 10,
                'data': [ ... ]
            }

        Methods:
            GET /jobs/<_id> - job details

        Parameters:
            _id (str): job _id to get details

        Returns:
            data element with job attributes, see
            :class:`core4.queue.job.CoreJob`.

        Raises:
            400: failed to parse job _id
            401: Unauthorized
            404: job not found

        Examples:
            >>> # continue example from above
            >>> _id = rv.json()["data"][0]["_id"]
            >>> get(url + "/jobs/" + _id, headers=h).json()
            {
                '_id': '5bdb09c6de8b691e497f00ab',
                'code': 200,
                'message': 'OK',
                'timestamp': '2018-11-01T14:12:22.283088',
                'data': {
                    '_id': '5bd72861de8b69147a275e22',
                    'args': {
                        'i': 4, 'sleep': 23
                    },
                    'attempts': 1,
                    'attempts_left': 1,
                    'enqueued': {
                        'at': '2018-10-29T15:33:53',
                        'hostname': 'mra.devops',
                        'parent_id': None,
                        'username': 'mra'
                    },
                    'finished_at': None,
                    'journal': False,
                    'killed_at': '2018-10-29T15:34:07.084000',
                    'locked': None,
                    'name': 'core4.queue.helper.DummyJob',
                    'priority': 0,
                    'removed_at': None,
                    'runtime': 21.0,
                    'started_at': '2018-10-29T15:33:54',
                    'state': 'killed',
                    'trial': 1,
                    'wall_at': None,
                    'zombie_at': None
                }
            }
        """
        if _id:
            oid = self.parse_id(_id)
            ret = await self.get_detail(oid)
            if not ret:
                raise HTTPError(404, "job _id [{}] not found".format(oid))
        else:
            ret = await self.get_listing()
        self.reply(ret)

    async def post(self, _id=None):
        """
        Same as ``GET``. Paginated job listing with ``/jobs`` and single job
        details with ``/jobs/<_id>``. Additionally this method parses a
        ``filter`` attribute to filter jobs.

        Methods:
            POST /jobs - jobs listing

        Parameters:
            per_page (int): number of jobs per page
            page (int): requested page (starts counting with ``0``)
            sort (str): sort field
            order (int): sort direction (``1`` for ascending, ``-1`` for
                         descending)
            filter (dict): MongoDB query

        Returns:
            see :meth:`.get`

        Raises:
            see :meth:`.get`

        Examples:
            >>> # example continues from above
            >>> args = {"page": "0", "filter": {"args.sleep": {"$lte": 5}}}
            >>> post(url + "/jobs", headers=h, json=args)
        """
        await self.get(_id)

    def parse_id(self, _id):
        """
        parses str into :class:`bson.objectid.ObjectId` and raises
        400 - Bad Request error in case of failure

        :param _id: _id (str)
        :return: _id as :class:`bson.objectid.ObjectId`.
        """
        try:
            return ObjectId(_id)
        except:
            raise HTTPError(400, "failed to parse job _id: [{}]".format(_id))

    async def get_listing(self):
        """
        Retrieve job listing from ``sys.queue``. Only jobs with read/execute
        access permissions granted to the current user are returned.

        :return: :class:`.PageResult`
        """

        per_page = int(self.get_argument("per_page", default=10))
        current_page = int(self.get_argument("page", default=0))
        query_filter = self.get_argument("filter", default={})
        sort_by = self.get_argument("sort", default="_id")
        sort_order = self.get_argument("order", default=1)

        data = []
        async for doc in self.collection("queue").find(query_filter).sort(
                [(sort_by, int(sort_order))]):
            if await self.user.has_job_access(doc["name"]):
                data.append(doc)

        async def _length(*args, **kwargs):
            return len(data)

        async def _query(skip, limit, *args, **kwargs):
            return data[skip:(skip + limit)]

        pager = CorePager(per_page=int(per_page),
                          current_page=int(current_page),
                          length=_length, query=_query,
                          #sort_by=[sort_by, int(sort_order)],
                          #filter=query_filter
        )
        return await pager.page()

    async def get_detail(self, _id):
        """
        Retrieve job listing from ``sys.queue`` and ``sys.journal`` using
        :meth:`.project_job_listing` to select job attributes. Only jobs with
        read/execute access permissions granted to the current user are
        returned.

        :param _id: job _id
        :return: dict of job attributes
        """
        doc = await self.collection("queue").find_one(
            filter={"_id": _id},
            projection=self.project_job_listing())
        if not doc:
            # fallback to journal
            doc = await self.collection("journal").find_one(
                filter={"_id": _id},
                projection=self.project_job_listing())
            if doc:
                doc["journal"] = True
        else:
            doc["journal"] = False
        if not doc:
            raise HTTPError(404, "job_id [%s] not found", _id)
        if await self.user.has_job_access(doc["name"]):
            return doc
        raise HTTPError(403)

    async def delete(self, _id=None):
        """
        Only jobs with execute access permissions granted to the current user
        can be deleted.

        Methods:
            DELETE /jobs/<_id> - delete job from ``sys.queue``

        Parameters:
            _id (str): job _id to delete

        Returns:
            data element with ``True`` for success, else ``False``

        Raises:
            400: failed to parse job _id
            400: requires job _id
            401: Unauthorized
            403: Forbidden
            404: job _id not found

        Examples:
            >>> # continue example from :meth:`.get`
            >>> from requests import delete
            >>> rv = delete(url + "/jobs/" + _id, headers=h)
            >>> rv.json()
            {
                '_id': '5bdb0cc8de8b691e4983c4dc',
                'code': 200,
                'data': True,
                'message': 'OK',
                'timestamp': '2018-11-01T14:25:12.747484'
            }
        """
        if _id:
            oid = self.parse_id(_id)
            if not await self.remove_job(oid):
                raise HTTPError(404, "job _id [%s] not found", oid)
        else:
            raise HTTPError(400, "requires job _id")
        self.reply(True)

    async def put(self, request=None):
        """
        Only jobs with execute access permissions granted to the current user
        can be updated.

        Methods:
            PUT /jobs/<action>/<_id> - manage job in ``sys.queue``

        Parameters:
            action(str): ``delete``, ``kill`` or ``restart``
            _id (str): job _id

        Returns:
            data element with

            - **OK** (str) for actions delete and kill
            - **_id** (str) with new job ``_id`` for action restart

        Raises:
            400: failed to parse job _id
            400: requires action and job _id
            400: failed to restart job
            401: Unauthorized
            403: Forbidden
            404: job _id not found

        Examples:
            >>> # continue example from :meth:`.get`
            >>> from requests import delete
            >>> rv = delete(url + "/jobs/" + _id, headers=h)
            >>> rv.json()
            {
                '_id': '5bdb0cc8de8b691e4983c4dc',
                'code': 200,
                'data': 'OK',
                'message': 'OK',
                'timestamp': '2018-11-01T14:25:12.747484'
            }
        """
        if request:
            parts = request.split("/")
            oid = self.parse_id(parts[-1])
            if len(parts) == 2:
                action = parts[0].lower()
            else:
                action = self.get_argument("action")
            action_method = {
                "delete": self.remove_job,
                "restart": self.restart_job,
                "kill": self.kill_job
            }
            if action not in action_method:
                raise HTTPError(
                    400, "requires action in (delete, restart, kill)")
            await self._access_by_id(oid)
            self.reply(await action_method[action](oid))
        raise HTTPError(400, "requires action and job_id")

    async def _access_by_id(self, oid):
        doc = await self.collection("queue").find_one(
            filter={"_id": oid},
            projection=["name"])
        if not doc:
            raise HTTPError(404, "job_id [%s] not found", oid)
        if not await self.user.has_job_exec_access(doc["name"]):
           raise HTTPError(403)

    async def update(self, oid, attr, message, event):
        """
        Update the passed job attribute, used with ``removed_at`` and
        ``killed_at``. Only jobs with execute access permissions granted to the
        current user  can be deleted.

        :param oid: :class:`bson.objectid.ObjectId` of the job
        :param attr: job attribute to update
        :param message: logging helper string
        :return: ``True`` for success, else ``False``
        """
        await self._access_by_id(oid)
        at = core4.util.node.mongo_now()
        ret =  await self.collection("queue").update_one(
            {
                "_id": oid,
                attr: None
            },
            update={
                "$set": {
                    attr: at
                }
            }
        )
        if ret.raw_result["n"] == 1:
            self.logger.warning(
                "flagged job [%s] to %s at [%s]", oid, message, at)
            await self.make_stat(event, str(oid))
            return True
        raise HTTPError(404, "failed to flag job [%s] to %s", oid, message)

    async def remove_job(self, oid):
        """
        Flag the passed job ``_id`` in ``removed_at``. Active workers process
        this flag and remove the job from ``sys.queue``.

        :param oid: :class:`bson.objectid.ObjectId` of the job
        :return: ``True`` for success, else ``False``
        """
        return await self.update(oid, "removed_at", "remove",
                                 "request_remove_job")

    async def kill_job(self, oid):
        """
        Flag the passed job ``_id`` in ``killed_at``. Active workers process
        this flag and kill the job.

        :param oid: :class:`bson.objectid.ObjectId` of the job
        :return: ``True`` for success, else ``False``
        """
        return await self.update(oid, "killed_at", "kill", "request_kill_job")

    async def restart_job(self, oid):
        """
        Restart jobs in state *waiting* (``pending``, ``failed``, ``deferred``)
        or journal and re-enqueue jobs in state *stopped* (``error``,
        ``killed``, ``inactive``)

        :param oid: :class:`bson.objectid.ObjectId` of the job
        :return: dict with ``old_id`` and ``new_id``
        """
        if await self.restart_waiting(oid):
            self.logger.warning('successfully restarted [%s]', oid)
            return {"old_id": oid, "new_id": oid}
        else:
            new_id = await self.restart_stopped(oid)
            if new_id:
                self.logger.warning('successfully restarted [%s] '
                                    'with [%s]', oid, new_id)
                return {"old_id": oid, "new_id": new_id}
        raise HTTPError(404, "failed to restart job [%s]", oid)

    async def restart_waiting(self, _id):
        """
        Restart jobs in state *waiting* (``pending``, ``failed``,
        ``deferred``).

        :param _id: :class:`bson.objectid.ObjectId` of the job
        :return: ``True`` for success, else ``False``
        """
        ret = await self.collection("queue").update_one(
            {
                "_id": _id,
                "state": {
                    "$in": STATE_WAITING
                }
            },
            update={
                "$set": {
                    "query_at": None
                }
            }
        )
        await self.make_stat("restart_waiting", str(_id))
        return ret.modified_count == 1

    async def restart_stopped(self, _id):
        """
        Restart job in state *stopped* (``error``, ``killed``, ``inactive``).

        :param _id: :class:`bson.objectid.ObjectId` of the job
        :return: new job _id
        """
        queue = self.collection("queue")
        job = await queue.find_one(filter={"_id": _id})
        if job:
            if job["state"] in STATE_STOPPED:
                if await self.lock_job(
                        self.application.container.identifier, _id):
                    ret = await queue.delete_one({"_id": _id})
                    if ret.raw_result["n"] == 1:
                        doc = dict([(k, v) for k, v in job.items() if
                                    k in core4.queue.job.ENQUEUE_ARGS])
                        new_job = self.queue.job_factory(job["name"], **doc)
                        new_job.__dict__[
                            "attempts_left"] = new_job.__dict__["attempts"]
                        new_job.__dict__[
                            "state"] = core4.queue.main.STATE_PENDING
                        new_job.__dict__["enqueued"] = self.who()
                        new_job.__dict__["enqueued"]["parent_id"] = job["_id"]
                        new_doc = new_job.serialise()
                        ret = await queue.insert_one(new_doc)
                        new_doc["_id"] = ret.inserted_id
                        self.logger.info(
                            'successfully enqueued [%s] with [%s]',
                            new_job.qual_name(), new_doc["_id"])
                        job["enqueued"]["child_id"] = new_doc["_id"]
                        await self.collection("journal").insert_one(job)
                        await self.collection("lock").delete_one({"_id": _id})
                        await self.make_stat("restart_stopped", str(_id))
                        return new_doc["_id"]
            raise HTTPError(400, "cannot restart job [%s] in state [%s]", _id,
                            job["state"])
        return None

    async def lock_job(self, identifier, _id):
        """
        Reserve the job for exclusive processing utilising collection
        ``sys.lock``.

        :param identifier: to assign to the reservation
        :param _id: job ``_id``
        :return: ``True`` if reservation succeeded, else ``False``
        """
        try:
            await self.collection("lock").insert_one(
                {"_id": _id, "owner": identifier})
            return True
        except pymongo.errors.DuplicateKeyError:
            return False
        except:
            raise

    def who(self):
        """
        Creates ``enqueued`` dict attribute with timestamp (``at``),
        ``hostname``, and ``username``.

        :return: dict
        """
        x_real_ip = self.request.headers.get("X-Real-IP")
        return {
            "at": core4.util.node.mongo_now(),
            "hostname": x_real_ip or self.request.remote_ip,
            "username": self.current_user
        }

    async def get_queue_count(self):
        """
        Retrieves aggregated information about ``sys.queue`` state. This is

        * ``n`` - the number of jobs in the given state
        * ``state`` - job state
        * ``flags`` - job flags ``zombie``, ``wall``, ``removed`` and
          ``killed``

        :return: dict
        """
        cur = self.collection("queue").aggregate(self.pipeline_queue_count())
        ret = {}
        async for doc in cur:
            ret[doc["state"]] = doc["n"]
        return ret

    async def make_stat(self, event, _id):
        """
        Collects current job state counts from ``sys.queue`` and inserts a
        record into ``sys.event``. See also :meth:`.CoreQueue.make_stat`.

        :param event: to log
        :param _id: job _id
        """
        self.trigger(name=event, channel=core4.const.QUEUE_CHANNEL,
                     data={"_id": _id, "queue": await self.get_queue_count()})


class JobPost(JobHandler):
    """
    Post new job.
    """

    author = "mra"
    title = "enqueue job"
    tag = ["job management"]

    async def post(self, _id=None):
        """
        Only jobs with execute access permissions granted to the current user
        can be posted.

        Methods:
            POST /enqueue - enqueue job

        Parameters:
            args (dict): arguments to be passed to the job
            attempts (int): maximum number of execution attempts after job
                            failure before the job enters the final ``error``
                            state
            chain (list of str): list of jobs to be started after successful
                                 job completion
            defer_time (int): seconds to wait before restart after defer
            defer_max (int): maximum number of seconds to defer the job before
                             the job turns inactive
            dependency (list of str): jobs which need to be completed before
                                      execution start
            error_time (int): seconds to wait before job restart after failure
            force (bool): if ``True`` then ignore worker resource limits and
                          launch the job
            max_parallel (int): maximum number jobs to run in parallel on the
                                same node
            priority (int): to execute the job with >0 higher and <0 lower
                            priority (defaults to 0)
            python (str): Python executable to be used for dedicated Python
                          virtual environment
            wall_time (int): number of seconds before a running job turns into
                             a non-stopping job
            worker (list of str): eligable to execute the job
            zombie_time (int): number of seconds before a job turns into a
                               zombie non-stopping job

        Returns:
            data element with

            - **_id**: of the enqueued job
            - **name**: of the enqueued job

        Raises:
            400: job exists with args
            401: Unauthorized
            403: Forbidden
            404: cannot instantiate job

        Examples:
            >>> from requests import post, get
            >>> signin = get(url + "/login?username=admin&password=hans")
            >>> token = signin.json()["data"]["token"]
            >>> h = {"Authorization": "Bearer " + token}
            >>> name = "core4.queue.helper.job.example.DummyJob"
            >>> rv = post(url + "/enqueue?name=" + name, headers=h)
            >>> rv.json()
            {
                '_id': '5bdb554fde8b6925830b8b39',
                'code': 200,
                'message': 'OK',
                'timestamp': '2018-11-01T19:34:39.542516',
                'data': {
                    '_id': '5bdb554fde8b6925830b8b3e',
                    'name': 'core4.queue.helper.DummyJob'
                }
            }
        """
        job = await self.enqueue()
        self.reply({
            "name": job.qual_name(),
            "_id": job._id
        })

    async def enqueue(self):
        """
        Enqueue job with name from argument.

        :return: enqueued :class:`core4.queue.job.CoreJob`` instance
        """
        name = self.get_argument("name")
        args = dict([
            (k, v[0]) for k, v
            in self.request.arguments.items()
            if k != "name"])
        try:
            job = self.queue.job_factory(name, **args)
        except Exception:
            exc_info = sys.exc_info()
            raise HTTPError(404, "cannot instantiate job [%s]: %s:\n%s",
                            name, repr(exc_info[1]),
                            traceback.format_exception(*exc_info))
        if not await self.user.has_job_exec_access(name):
            raise HTTPError(403)
        job.__dict__["attempts_left"] = job.__dict__["attempts"]
        job.__dict__["state"] = core4.queue.job.STATE_PENDING
        job.__dict__["enqueued"] = self.who()
        doc = job.serialise()
        try:
            ret = await self.collection("queue").insert_one(doc)
        except pymongo.errors.DuplicateKeyError:
            raise HTTPError(400, "job [%s] exists with args %s",
                            job.qual_name(), job.args)
        job.__dict__["_id"] = ret.inserted_id
        job.__dict__["identifier"] = ret.inserted_id
        self.logger.info(
            'successfully enqueued [%s] with [%s]', job.qual_name(), job._id)
        await self.make_stat("enqueue_job", str(job._id))
        return job


class JobStream(JobPost):
    """
    Stream job attributes until job reached final state (``ERROR``,
    ``INACTIVE``, ``KILLED``).
    """

    author = "mra"
    title = "job state stream"
    tag = ["job management"]

    async def enter(self):
        raise HTTPError(400, "You cannot directly enter this endpoint. "
                             "You must provide a job ID")

    async def get(self, _id=None):
        """
        Only jobs with execute access permissions granted to the current user
        can be streamed.

        Methods:
            GET /jobs/poll/<_id> - stream job attributes

        Parameters:
            _id (str): job _id

        Returns:
            JSON stream with job attributes

        Raises:
            401 Bad Request: failed to parse job _id
            401 Unauthorized
            403 Forbidden
            404 cannot instantiate job

        Examples:
            >>> from requests import post, get
            >>> import json
            >>> rv = post(url + "/enqueue?name=" + name, headers=h, json={"sleep": 20})
            >>> _id = rv.json()["data"]["_id"]
            >>> rv = get(url + "/jobs/poll/" + _id, headers=h, stream=True)
            >>> for line in rv.iter_lines():
            >>>     if line:
            >>>         data = json.loads(line.decode("utf-8"))
            >>>         locked = data.get("locked")
            >>>         state = data.get("state")
            >>>         if locked:
            >>>             print(locked["progress_value"], state)
            0.00045184999999996477 running
            0.2524361 running
            0.5028721 running
            0.75340995 running
        """
        if _id == "" or _id is None:
            raise HTTPError(400, "failed to parse job _id: [{}]".format(_id))
        self.set_header('content-type', 'text/event-stream')
        self.set_header('cache-control', 'no-cache')
        oid = self.parse_id(_id)
        last = None
        exit = False
        while not exit:
            doc = await self.get_detail(oid)
            if doc["state"] in STATE_FINAL:
                exit = True
                self.finish(doc)
            elif last is None or doc != last:
                last = doc
                js = json_encode(doc, indent=None, separators=(',', ':'))
                try:
                    self.write(js + "\n\n")
                    self.logger.info(
                        "serving [%s] with [%d] byte",
                        self.current_user, len(js))
                    await self.flush()
                except StreamClosedError:
                    self.logger.info("stream closed")
                    exit = True
                except Exception:
                    self.logger.error("stream error", exc_info=True)
                    exit = True
            await gen.sleep(1.)

    async def post(self, _id=None):
        """
        Only jobs with execute access permissions granted to the current user
        can be enqueued and streamed.

        Methods:
            POST /jobs/poll - enqueue job and stream job progress

        Parameters:
            args (dict): arguments to be passed to the job
            attempts (int): maximum number of execution attempts after job
                            failure before the job enters the final ``error``
                            state
            chain (list of str): list of jobs to be started after successful
                                 job completion
            defer_time (int): seconds to wait before restart after defer
            defer_max (int): maximum number of seconds to defer the job before
                             the job turns inactive
            dependency (list of str): jobs which need to be completed before
                                      execution start
            error_time (int): seconds to wait before job restart after failure
            force (bool): if ``True`` then ignore worker resource limits and
                          launch the job
            max_parallel (int): maximum number jobs to run in parallel on the
                                same node
            priority (int): to execute the job with >0 higher and <0 lower
                            priority (defaults to 0)
            python (str): Python executable to be used for dedicated Python
                          virtual environment
            wall_time (int): number of seconds before a running job turns into
                             a non-stopping job
            worker (list of str): eligable to execute the job
            zombie_time (int): number of seconds before a job turns into a
                               zombie non-stopping job

        Returns:
            JSON stream with job attributes

        Raises:
            400: failed to parse job _id
            401: Unauthorized
            403: Forbidden
            404: job not found

        Examples:
            >>> from requests import post, get
            >>> signin = get(url + "/login?username=admin&password=hans")
            >>> token = signin.json()["data"]["token"]
            >>> h = {"Authorization": "Bearer " + token}
            >>> name = "core4.queue.helper.DummyJob"
            >>> rv = post(url + "/jobs/poll?name=" + name, headers=h, json={"sleep": 20}, stream=True)
            >>> for line in rv.iter_lines():
            >>>     if line:
            >>>         data = json.loads(line.decode("utf-8"))
            >>>         locked = data.get("locked")
            >>>         state = data.get("state")
            >>>         print("{:6.2f}% - {}".format(
            >>>             locked["progress_value"] * 100. if locked else 100,
            >>>             state))
            100.00% - pending
              0.04% - running
             25.13% - running
             50.18% - running
             75.28% - running
        """
        job = await self.enqueue()
        await self.get(job._id)
