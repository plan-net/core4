from tornado.web import HTTPError

import core4.util.node
from core4.api.v1.application import CoreApiContainer, serve
from core4.api.v1.request.main import CoreRequestHandler

# see API definition at
# https://docs.google.com/document/d/18xyMu5TsJCpkPFtU75nTGvYKUs3dE1uGFdQiWz8HImM/edit?usp=sharing

class BaseHandler(CoreRequestHandler):
    protected = False

    async def prepare_protection(self):
        token = self.get_argument("token", as_type=str)
        if token != self.config.example.auth_token:
            self.write_error(401)

    def collection(self, name):
        if name not in self.__dict__:
            coll = self.config.example.collection[name]
            self.__dict__[name] = coll.connect_async()
        return self.__dict__[name]

    @property
    def client_collection(self):
        return self.collection("client")

    @property
    def session_collection(self):
        return self.collection("session")

    @property
    def event_collection(self):
        return self.collection("event")

    async def get_current(self):
        doc = await self.session_collection.find_one({"state": "OPEN"})
        if doc is None:
            raise HTTPError(404, "no open session")
        return doc


class RegisterHandler(BaseHandler):
    author = 'mra'

    async def post(self):
        _id = self.get_argument("_id", as_type=str)
        now = core4.util.node.mongo_now()
        ret = await self.client_collection.update_one(
            {
                "_id": _id,
            },
            update={
                "$set": {
                    "updated_at": now
                },
                "$setOnInsert": {
                    "created_at": now
                },
            },
            upsert=True
        )
        self.reply({"_id": _id, "created": ret.upserted_id is not None})


class SessionHandler(BaseHandler):
    author = 'mra'

    async def post(self, session_id):
        doc = {
            "question": self.get_argument("question", as_type=str),
            "data": self.get_argument("data", as_type=dict, default={}),
            "state": "CLOSED"
        }
        await self.session_collection.insert_one(doc)
        doc["session_id"] = doc.pop("_id")
        self.reply(doc)

    async def get(self, session_id):
        if session_id:
            oid = self.parse_objectid(session_id)
            doc = await self.session_collection.find_one({"_id": oid})
            doc["session_id"] = doc.pop("_id")
            self.reply(doc)
        else:
            ret = []
            async for doc in self.session_collection.find().sort(
                    "question", 1):
                doc["session_id"] = doc.pop("_id")
                ret.append(doc)
            self.reply(ret)

    async def delete(self, session_id):
        oid = self.parse_objectid(session_id)
        ret = await self.session_collection.delete_one({"_id": oid})
        if ret.deleted_count != 1:
            raise HTTPError(404, "session_id [{}] not found".format(
                session_id))
        self.reply(True)

    async def put(self, session_id):
        oid = self.parse_objectid(session_id)
        question = self.get_argument("question", as_type=str, default=None)
        data = self.get_argument("data", as_type=dict, default=None)
        doc = {}
        if question is not None:
            doc["question"] = question
        if data is not None:
            doc["data"] = data
        if doc == {}:
            raise HTTPError(400, "PUT requires question and/or data")
        ret = await self.session_collection.update_one(
            {
                "_id": oid
            },
            update={
                "$set": doc
            }
        )
        if ret.matched_count != 1:
            raise HTTPError(404, "session_id [{}] not found".format(
                session_id))
        await self.get(session_id)


class StartSessionHandler(SessionHandler):
    author = 'mra'

    async def post(self, session_id):
        await self.close_current()
        oid = self.parse_objectid(session_id)
        now = core4.util.node.mongo_now()
        ret = await self.session_collection.update_one(
            {
                "_id": oid
            },
            update={
                "$set": {
                    "state": "OPEN",
                    "started_at": now
                }
            }
        )
        if ret.modified_count != 1:
            raise HTTPError(404, "session_id [{}] not found".format(
                session_id))
        await self.get(session_id)

    async def delete(self, session_id):
        if await self.close_current():
            await self.get(session_id)
        else:
            raise HTTPError(400, "no session open")

    async def close_current(self):
        now = core4.util.node.mongo_now()
        ret = await self.session_collection.update_many(
            {
                "state": "OPEN"
            },
            update={
                "$set": {
                    "state": "CLOSED",
                    "closed_at": now
                }
            }
        )
        return ret.modified_count == 1

class StopSessionHandler(StartSessionHandler):
    author = 'mra'

    async def post(self, session_id):
        await self.delete(session_id)


class EventHandler(BaseHandler):
    author = 'mra'

    async def post(self):
        _id = self.get_argument("id", as_type=str)
        data = self.get_argument("data", as_type=dict, default={})
        now = core4.util.node.mongo_now()
        session = await self.get_current()
        ret = await self.event_collection.update_one(
            {
                "client_id": _id,
                "session_id": session["_id"]
            },
            update={
                "$set": {
                    "timestamp": now,
                    "data": data
                },
                "$setOnInsert": {
                    "created_at": now
                },
            },
            upsert=True
        )
        if ret.upserted_id is not None:
            self.set_status(201)
        elif ret.modified_count == 1:
            self.set_status(200)
        self.reply(True)


class SessionStateHandler(BaseHandler):
    author = 'mra'

    def initialize(self):
        super().initialize()
        self.set_header('content-type', 'text/event-stream')
        self.set_header('cache-control', 'no-cache')

    async def get(self, session_id=None):
        oid = self.parse_id(session_id)
        # last = None
        # exit = False
        # while not exit:
        #     doc = await self.get_detail(oid)
        #     if doc["state"] in STATE_FINAL:
        #         exit = True
        #         self.finish(doc)
        #     elif last is None or doc != last:
        #         last = doc
        #         js = json_encode(doc, indent=None, separators=(',', ':'))
        #         try:
        #             self.write(js + "\n\n")
        #             self.logger.info(
        #                 "serving [%s] with [%d] byte",
        #                 self.current_user, len(js))
        #             await self.flush()
        #         except StreamClosedError:
        #             self.logger.info("stream closed")
        #             exit = True
        #         except Exception:
        #             self.logger.error("stream error", exc_info=True)
        #             exit = True
        #     await gen.sleep(1.)



class VotingApp(CoreApiContainer):
    root = "/voting/v1"
    rules = [
        ("/register", RegisterHandler),
        ("/session/?(.*)", SessionHandler),
        ("/start/?(.*)", StartSessionHandler),
        ("/stop/?(.*)", StopSessionHandler),
        ("/event", EventHandler),
        ("/poll/?(.*)", SessionStateHandler),
    ]


if __name__ == '__main__':
    serve(VotingApp, debug=True)

# count all sessions
# list(local_db.voting.event.aggregate([{"$group": {"_id": "$session_id", "n": {"$sum": 1}}}]))

# count one session
# list(local_db.voting.event.aggregate([{"$match": {"session_id": ObjectId("5be958b8de8b6975631ff7f0")}}, {"$group": {"_id": "$session_id", "n": {"$sum": 1}}}]))

# time series of one session
# list(local_db.voting.event.aggregate([{"$match": {"session_id": ObjectId("5be958b8de8b6975631ff7f0")}}, {"$group": {"_id": "$timestamp", "n": {"$sum": 1}}}, {"$sort": {"_id": 1}}]))
