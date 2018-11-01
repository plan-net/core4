import pymongo
import pymongo.errors
from bson.objectid import ObjectId
from tornado import gen
from tornado.iostream import StreamClosedError
from tornado.web import HTTPError

import core4.queue.job
import core4.queue.query
import core4.util
from core4.api.v1.request.main import CoreRequestHandler
from core4.api.v1.util import json_encode
from core4.queue.main import CoreQueue

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
            self._collection[name] = self.config.sys[name].connect_async()
        return self._collection[name]

    async def get(self, _id=None):
        """
        Job listing with ``/jobs`` and job details with ``/jobs/<_id>``.

        Methods:
            /jobs - jobs listing

        Parameters:
            None

        Returns:
            data element wirh job attributes, see :ref:`job_attributes`

        Errors:
            401: Unauthorized

        Examples:
            >>> from requests import get, post
            >>> url = "http://localhost:5001/core4/api/v1"
            >>> signin = get(url + "/login?username=admin&password=hans")
            >>> token = signin.json()["data"]["token"]
            >>> h = {"Authorization": "Bearer " + token}
            >>> rv = get(url + "/jobs", headers=h)
            >>> rv.json()
            {
                '_id': '5bdaf01ade8b691e49e19558',
                'code': 200,
                'message': 'OK',
                'timestamp': '2018-11-01T12:22:50.131383',
                'data': [
                    {
                        '_id': '5bd72861de8b69147a275e22',
                        'args': {
                            'i': 4,
                            'sleep': 23
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
                    },
                    {
                        '_id': '5bdaef7ede8b691db888cb36',
                        'args': {
                            'i': 4, 'sleep': 10
                        },
                        'attempts': 1,
                        'attempts_left': 1,
                        'enqueued': {
                            'at': '2018-11-01T12:20:14',
                            'hostname': 'mra.devops',
                            'parent_id': None,
                            'username': 'mra'
                        },
                        'finished_at': None,
                        'killed_at': None,
                        'locked': None,
                        'name': 'core4.queue.helper.DummyJob',
                        'priority': 0,
                        'removed_at': None,
                        'runtime': None,
                        'started_at': None,
                        'state': 'pending',
                        'trial': 0,
                        'wall_at': None,
                        'zombie_at': None
                    }
                ]
            }

        Methods:
            ``/jobs/<_id>`` - jobs details

        Parameters:
            _id (str): job _id to get details

        Returns:
            data element with job attributes, see :ref:`job_attributes`

        Errors:
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
            self.abort(400, "failed to parse job _id [{}]".format(_id))

    async def get_listing(self):
        """
        Retrieve job listing from ``sys.queue`` using
        :meth:`.project_job_listing` to select job attributes.

        :return: list of dict
        """
        # todo: requires pagination
        cur = self.collection("queue").find(
            projection=self.project_job_listing()).sort("_id", 1)
        ret = []
        async for doc in cur:
            ret.append(doc)
        return ret

    async def get_detail(self, _id):
        """
        Retrieve job listing from ``sys.queue`` and ``sys.journal`` using
        :meth:`.project_job_listing` to select job attributes.

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
            raise HTTPError(404, "job_id [{}] not found".format(_id))
        return doc

    async def delete(self, _id=None):
        """
        Methods:
            ``/jobs/<_id>`` - delete job from ``sys.queue``

        Parameters:
            _id (str): job _id to delete

        Returns:
            data element with ``True`` for success, else ``False``

        Errors:
            400: failed to parse job _id
            400: requires job _id
            401: Unauthorized
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
                raise HTTPError(404, "job _id [{}] not found".format(oid))
        else:
            raise HTTPError(400, "requires job _id")
        self.reply(True)

    async def put(self, request=None):
        """
        Methods:
            ``/jobs/<action>/<_id>`` - manage job in ``sys.queue``, this is
            delete, kill and restart.

        Parameters:
            action(str): ``delete``, ``kill`` or ``restart``
            _id (str): job _id

        Returns:
            data element with

            - **OK** (str) for actions delete and kill
            - **_id** (str) with new job ``_id`` for action restart

        Errors:
            400: failed to parse job _id
            400: requires action and job _id
            400: failed to restart job
            401: Unauthorized
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
                self.abort(400, "requires action in (delete, restart, kill)")
            self.reply(await action_method[action](oid))
        raise HTTPError(400, "requires action and job_id")

    async def update(self, oid, attr, message):
        """
        Update the passed job attribute, used with ``removed_at`` and
        ``killed_at``

        :param oid: :class:`bson.objectid.ObjectId` of the job
        :param attr: job attribute to update
        :param message: logging helper string
        :return: ``True`` for success, else ``False``
        """
        at = core4.util.now()
        ret = await self.collection("queue").update_one(
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
            return True
        raise HTTPError(404, "failed to flag job [%s] to %s" % (oid, message))

    async def remove_job(self, oid):
        """
        Flag the passed job ``_id`` in ``removed_at``. Active workers process
        this flag and remove the job from ``sys.queue``.

        :param oid: :class:`bson.objectid.ObjectId` of the job
        :return: ``True`` for success, else ``False``
        """
        return await self.update(oid, "removed_at", "remove")

    async def kill_job(self, oid):
        """
        Flag the passed job ``_id`` in ``killed_at``. Active workers process
        this flag and kill the job.

        :param oid: :class:`bson.objectid.ObjectId` of the job
        :return: ``True`` for success, else ``False``
        """
        return await self.update(oid, "killed_at", "kill")

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
        raise HTTPError(404, "failed to restart job [%s]" % oid)

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
                        await self.make_stat()
                        return new_doc["_id"]
            raise HTTPError(400, "cannot restart job [%s] in state [%s]" % (
                _id, job["state"]
            ))
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

    async def make_stat(self):
        """
        Collects current job state counts from ``sys.queue`` and inserts a
        record into ``sys.stat``.
        """
        state = await self.get_queue_count()
        state["timestamp"] = core4.util.now().timestamp()
        await self.collection("stat").insert_one(state)

    def who(self):
        """
        Creates ``enqueued`` dict attribute with timestamp (``at``),
        ``hostname``, and ``username``.

        :return: dict
        """
        x_real_ip = self.request.headers.get("X-Real-IP")
        return {
            "at": core4.util.mongo_now(),
            "hostname": x_real_ip or self.request.remote_ip,
            "username": self.current_user
        }

    async def post(self, _id=None):
        """
        Methods:
            ``/jobs/<_id>`` - enqueue job

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

        Errors:
            400: job exists with args
            401: Unauthorized
            404: cannot instantiate job

        Examples:
            >>> from requests import post, get
            >>> signin = get(url + "/login?username=admin&password=hans")
            >>> token = signin.json()["data"]["token"]
            >>> h = {"Authorization": "Bearer " + token}
            >>> name = "core4.queue.helper.DummyJob"
            >>> rv = post(url + "/jobs?name=" + name, headers=h)
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
            self.abort(404, "cannot instantiate job [{}]".format(name))
        job.__dict__["attempts_left"] = job.__dict__["attempts"]
        job.__dict__["state"] = core4.queue.job.STATE_PENDING
        job.__dict__["enqueued"] = self.who()
        doc = job.serialise()
        try:
            ret = await self.collection("queue").insert_one(doc)
        except pymongo.errors.DuplicateKeyError:
            self.abort(400, "job [{}] exists with args {}".format(
                job.qual_name(), job.args))
        job.__dict__["_id"] = ret.inserted_id
        job.__dict__["identifier"] = ret.inserted_id
        self.logger.info(
            'successfully enqueued [%s] with [%s]', job.qual_name(), job._id)
        state = await self.get_queue_count()
        state["timestamp"] = core4.util.now().timestamp()
        await self.collection("stat").insert_one(state)
        return job

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


class JobStream(JobHandler):

    def initialize(self):
        super().initialize()
        self.set_header('content-type', 'text/event-stream')
        self.set_header('cache-control', 'no-cache')

    async def get(self, _id=None):
        """
        Methods:
            ``/jobs/poll`` - stream job attributes

        Parameters:
            None

        Returns:
            JSON stream with job attributes

        Errors:
            400: job exists with args
            401: Unauthorized
            404: cannot instantiate job

        Examples:
            >>> rv = post(url + "/jobs?name=" + name, headers=h, json={"sleep": 20})
            >>> _id = rv.json()["data"]["_id"]
            >>> rv = get(url + "/jobs/poll/" + _id, headers=h, stream=True)
            >>> for line in rv.iter_lines():
            >>>     if line:
            >>>         data = json.loads(line.decode("utf-8"))
            >>>         locked = data.get("locked")
            >>>         state = data.get("state")
            >>>         print("{:6.2f}% - {}".format(locked["progress_value"] * 100. if locked else 100, state))
            100.00% - pending
              0.04% - running
             25.13% - running
             50.17% - running
             75.22% - running
            100.00% - complete
        """
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
        Methods:
            ``/jobs/poll`` - enqueue job and stream job progress

        Parameters:
            see ``POST`` of :class:`core4.api.v1.request.queue.job.JobHandler`

        Returns:
            JSON stream with job attributes

        Errors:
            400: failed to parse job _id
            401: Unauthorized
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
