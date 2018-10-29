import pymongo

import core4.util
from core4.api.v1.request.main import CoreRequestHandler
from core4.queue.job import STATE_PENDING
from core4.queue.main import CoreQueue
import core4.queue.query
from bson.objectid import ObjectId
from tornado.web import HTTPError


class JobHandler(CoreRequestHandler, core4.queue.query.QueryMixin):

    def initialize(self):
        self.queue = CoreQueue()

    async def get(self, _id=None):
        coll = self.config.sys.queue.connect_async()
        if _id:
            ret = await self.get_detail(coll, _id[1:])
            if not ret:
                raise HTTPError(404, "job_id [{}] not found".format(_id[1:]))
        else:
            ret = await self.get_listing(coll)
        self.reply(ret)

    async def get_listing(self, coll):
        cur = coll.find(
            projection=self.project_job_listing()).sort("_id", 1)
        ret = []
        async for doc in cur:
            ret.append(doc)
        return ret

    async def get_detail(self, coll, _id):
        try:
            oid = ObjectId(_id)
        except:
            self.abort(400, "bad job_id [{}]".format(_id))
        doc = await coll.find_one(
            filter={"_id": oid },
            projection=self.project_job_listing())
        if not doc:
            raise HTTPError(404, "job_id [{}] not found".format(_id[1:]))
        return doc

    async def post(self, _id=None):
        name = self.get_argument("name")
        args = dict([
            (k, v[0]) for k, v
            in self.request.arguments.items()
            if k != "name"])
        job = await self.enqueue(name, **args)
        self.reply({
            "name": job.qual_name(),
            "_id": job._id
        })

    async def enqueue(self, name, **kwargs):
        try:
            job = self.queue.job_factory(name, **kwargs)
        except Exception as exc:
            self.abort(400, "cannot instantiate job [{}]".format(name))
        job.__dict__["attempts_left"] = job.__dict__["attempts"]
        job.__dict__["state"] = STATE_PENDING
        # todo: extract remote ip
        job.__dict__["enqueued"] = {
            "at": core4.util.mongo_now(),
            "hostname": None,
            "parent_id": None,
            "username": self.current_user
        }
        doc = job.serialise()
        coll = self.config.sys.queue.connect_async()
        try:
            ret = await coll.insert_one(doc)
        except pymongo.errors.DuplicateKeyError:
            self.abort(400, "job [{}] exists with args {}".format(
                    job.qual_name(), job.args))
        job.__dict__["_id"] = ret.inserted_id
        job.__dict__["identifier"] = ret.inserted_id
        self.logger.info(
            'successfully enqueued [%s] with [%s]', job.qual_name(), job._id)
        state = await self.get_queue_count(coll)
        state["timestamp"] = core4.util.now().timestamp()
        stat_coll = self.config.sys.stat.connect_async()
        await stat_coll.insert_one(state)
        return job

    async def get_queue_count(self, coll):
        """
        Retrieves aggregated information about ``sys.queue`` state. This is


        * ``n`` - the number of jobs in the given state
        * ``state`` - job state
        * ``flags`` - job flags ``zombie``, ``wall``, ``removed`` and
          ``killed``

        :return: dict
        """
        cur = coll.aggregate(self.pipeline_queue_count())
        ret = {}
        async for doc in cur:
            ret[doc["state"]] = doc["n"]
        return ret

