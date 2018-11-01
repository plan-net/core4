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
        self.sys_queue = self.config.sys.queue.connect_async()
        self.exit = False

    async def get(self, _id=None):
        if _id:
            try:
                oid = ObjectId(_id)
            except:
                self.abort(400, "bad job_id [{}]".format(_id))
            ret = await self.get_detail(oid)
            if not ret:
                raise HTTPError(404, "job_id [{}] not found".format(oid))
        else:
            ret = await self.get_listing()
        self.reply(ret)

    async def delete(self, _id=None):
        if _id:
            try:
                oid = ObjectId(_id)
            except:
                self.abort(400, "bad job_id [{}]".format(_id))
            ret = await self._remove_job(oid)
            if not ret:
                raise HTTPError(404, "job_id [{}] not found".format(oid))
        else:
            raise HTTPError(400, "requires job_id")
        self.reply("OK")

    async def put(self, request=None):
        if request:
            parts = request.split("/")
            try:
                oid = ObjectId(parts[-1])
            except:
                self.abort(400, "bad job_id [{}]".format(parts[-1]))
            if len(parts) == 2:
                action = parts[0].lower()
            else:
                action = self.get_argument("action")
            action_method = {
                "delete": self._remove_job,
                "restart": self._restart_job,
                "kill": self._kill_job
            }
            if action not in action_method:
                self.abort(400, "requires action in (delete, restart, kill)")
            ret = await action_method[action](oid)
            if not ret:
                raise HTTPError(404, "job_id [{}] not found".format(oid))
        else:
            raise HTTPError(400, "requires action and job_id")
        self.reply(ret)

    async def _update(self, oid, attr, message):
        at = core4.util.now()
        ret = await self.sys_queue.update_one(
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
            return oid
        self.logger.error("failed to flag job [%s] to %s", oid, message)
        return None

    async def _remove_job(self, oid):
        return await self._update(oid, "removed_at", "remove")

    async def _kill_job(self, oid):
        return await self._update(oid, "killed_at", "kill")

    async def _restart_job(self, oid):
        if await self._restart_waiting(oid):
            self.logger.warning('successfully restarted [%s]', oid)
            return oid
        else:
            new_id = await self._restart_stopped(oid)
            if new_id:
                self.logger.warning('successfully restarted [%s] '
                                    'with [%s]', oid, new_id)
                return new_id
        self.logger.error("failed to restart [%s]", oid)
        return None

    async def _restart_waiting(self, _id):
        # internal method used by ._restart_job
        ret = await self.sys_queue.update_one(
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

    async def _lock_job(self, identifier, _id):
        try:
            await self.config.sys.lock.connect_async().insert_one({
                "_id": _id, "owner": identifier})
            return True
        except pymongo.errors.DuplicateKeyError:
            return False
        except:
            raise

    async def _make_stat(self):
        state = await self.get_queue_count()
        state["timestamp"] = core4.util.now().timestamp()
        await self.config.sys.stat.connect_async().insert_one(state)

    async def _restart_stopped(self, _id):
        job = await self.sys_queue.find_one(filter={"_id": _id})
        if job["state"] in STATE_STOPPED:
            if await self._lock_job(
                    self.application.container.identifier, _id):
                ret = await self.sys_queue.delete_one({"_id": _id})
                if ret.raw_result["n"] == 1:
                    doc = dict([(k, v) for k, v in job.items() if
                                k in core4.queue.job.ENQUEUE_ARGS])
                    new_job = self.queue.job_factory(job["name"], **doc)
                    new_job.__dict__["attempts_left"] = new_job.__dict__[
                        "attempts"]
                    new_job.__dict__["state"] = core4.queue.main.STATE_PENDING
                    new_job.__dict__["enqueued"] = self._who()
                    new_job.__dict__["enqueued"]["parent_id"] = job["_id"]
                    new_doc = new_job.serialise()
                    try:
                        ret = await self.sys_queue.insert_one(new_doc)
                    except pymongo.errors.DuplicateKeyError:
                        raise core4.error.CoreJobExists(
                            "job [{}] exists with args {}".format(
                                new_job.qual_name(), new_job.args))
                    new_doc["_id"] = ret.inserted_id
                    self.logger.info(
                        'successfully enqueued [%s] with [%s]',
                        new_job.qual_name(), new_doc["_id"])
                    job["enqueued"]["child_id"] = new_doc["_id"]
                    await self.config.sys.journal.connect_async().insert_one(
                        job)
                    await self._make_stat()
                    return new_doc["_id"]
        return None

    async def get_listing(self):
        cur = self.sys_queue.find(
            projection=self.project_job_listing()).sort("_id", 1)
        ret = []
        async for doc in cur:
            ret.append(doc)
        return ret

    async def get_detail(self, _id):
        doc = await self.sys_queue.find_one(
            filter={"_id": _id},
            projection=self.project_job_listing())
        if not doc:
            # fallback to journal
            journal = self.config.sys.journal.connect_async()
            doc = await journal.find_one(
                filter={"_id": _id},
                projection=self.project_job_listing())
            if not doc:
                raise HTTPError(404, "job_id [{}] not found".format(_id))
            doc["journal"] = True
        else:
            doc["journal"] = False
        if not doc:
            raise HTTPError(404, "job_id [{}] not found".format(_id))
        if doc["state"] in STATE_FINAL:
            self.exit = True
        return doc

    async def post(self, _id=None):
        job = await self._enqueue()
        self.reply({
            "name": job.qual_name(),
            "_id": job._id
        })

    def _who(self):
        x_real_ip = self.request.headers.get("X-Real-IP")
        return {
            "at": core4.util.mongo_now(),
            "hostname": x_real_ip or self.request.remote_ip,
            "parent_id": None,
            "username": self.current_user
        }

    async def _enqueue(self):
        name = self.get_argument("name")
        args = dict([
            (k, v[0]) for k, v
            in self.request.arguments.items()
            if k != "name"])
        try:
            job = self.queue.job_factory(name, **args)
        except Exception:
            self.abort(400, "cannot instantiate job [{}]".format(name))
        job.__dict__["attempts_left"] = job.__dict__["attempts"]
        job.__dict__["state"] = core4.queue.job.STATE_PENDING
        job.__dict__["enqueued"] = self._who()
        doc = job.serialise()
        try:
            ret = await self.sys_queue.insert_one(doc)
        except pymongo.errors.DuplicateKeyError:
            self.abort(400, "job [{}] exists with args {}".format(
                job.qual_name(), job.args))
        job.__dict__["_id"] = ret.inserted_id
        job.__dict__["identifier"] = ret.inserted_id
        self.logger.info(
            'successfully enqueued [%s] with [%s]', job.qual_name(), job._id)
        state = await self.get_queue_count()
        state["timestamp"] = core4.util.now().timestamp()
        stat_coll = self.config.sys.stat.connect_async()
        await stat_coll.insert_one(state)
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
        cur = self.sys_queue.aggregate(self.pipeline_queue_count())
        ret = {}
        async for doc in cur:
            ret[doc["state"]] = doc["n"]
        return ret


class JobStream(JobHandler):

    def initialize(self):
        super().initialize()
        self.set_header('content-type', 'text/event-stream')
        self.set_header('cache-control', 'no-cache')
        self.exit = False

    async def _poll(self, meth, *args):
        last = None
        while not self.exit:
            doc = await meth(*args)
            if last is None or doc != last:
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
                    self.exit = True
                except Exception:
                    self.logger.error("stream error", exc_info=True)
                    self.exit = True
            await gen.sleep(1.)

    async def get(self, _id=None):
        if _id:
            try:
                oid = ObjectId(_id)
            except:
                self.abort(400, "bad job_id [{}]".format(_id))
            await self._poll(self.get_detail, oid)
        else:
            await self._poll(self.get_listing)
        self.reply(None)

    async def post(self, _id=None):
        job = await self._enqueue()
        await self.get(job._id)
