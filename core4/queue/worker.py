import os
import subprocess
import sys
import traceback
import psutil

from datetime import timedelta
import pymongo
import pymongo.errors
import time

import core4.base
import core4.error
import core4.queue.job
import core4.queue.main
import core4.service.setup
import core4.util

STEPS = (
    "work_jobs",
    "remove_jobs",
    "flag_jobs",
    "collect_stats")


class CoreWorker(core4.base.CoreBase):

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.identifier = kwargs.get("name", core4.util.get_hostname())
        self.hostname = core4.util.get_hostname()
        self.phase = {
            "startup": core4.util.now(),
            "loop": None,
            "shutdown": None,
            "exit": None
        }
        self.plan = None
        self.exit = False
        self.at = None
        self.cycle = dict([(s, 0) for s in STEPS])
        self.cycle["total"] = 0
        self.offset = None
        self.queue = core4.queue.main.CoreQueue()

    def start(self):
        self.register_worker()
        self.enter_phase("startup")
        self.create_worker_env()
        self.register_projects()
        self.cleanup()
        self.plan = self.create_plan()
        self.loop()
        self.cleanup()
        self.shutdown()
        self.enter_phase("exit")

    def create_worker_env(self):
        setup = core4.service.setup.CoreSetup()
        setup.make_folder()
        setup.make_role()  # todo: implement!
        self.create_stats()

    def create_stats(self):
        pass

    def register_worker(self):
        ret = self.config.sys.worker.update_one(
            {"_id": self.identifier},
            update={
                "$set": {
                    "phase": {},
                    "heartbeat": None,
                    "plugins": None
                }
            },
            upsert=True
        )
        if ret.raw_result["n"] == 1:
            self.logger.info("registered worker")
        else:
            raise core4.error.Core4SetupError("failed to register worker")

    def register_projects(self):
        # todo: implement
        pass

    def cleanup(self):
        ret = self.config.sys.lock.delete_many({
            "worker": self.identifier
        })
        self.logger.info("cleanup removed [%d] sys.lock records",
                         ret.raw_result["n"])

    def create_plan(self):
        plan = []
        now = core4.util.now()
        self.wait_time = None
        for s in STEPS:
            interval = self.config.worker.execution_plan[s]
            if self.wait_time is None:
                self.wait_time = interval
            else:
                self.wait_time = min(interval, self.wait_time)
            self.logger.debug("set [%s] interval [%1.2f] seconds",
                              s, interval)
            plan.append({
                "name": s,
                "interval": interval,
                "next": now + timedelta(seconds=interval),
                "call": getattr(self, s)
            })
        return plan

    def enter_phase(self, phase):
        self.phase[phase] = core4.util.now()
        ret = self.config.sys.worker.update_one(
            {"_id": self.identifier},
            update={
                "$set": {
                    "phase.{}".format(phase): self.phase[phase]
                }
            }
        )
        if ret.raw_result["n"] == 1:
            self.logger.info("enter phase [%s]", phase)
        else:
            raise core4.error.Core4SetupError(
                "failed to enter phase [{}]".format(phase))

    def loop(self):
        time.sleep(self.wait_time)  # start with cycle 1
        self.enter_phase("loop")
        in_maintenance = False
        while not self.exit:
            self.cycle["total"] += 1
            if self.queue.halt(self.phase["startup"]):
                return
            if self.queue.maintenance():
                if not in_maintenance:
                    in_maintenance = True
                    self.logger.info("enter maintenance")
            else:
                if in_maintenance:
                    in_maintenance = False
                    self.logger.info("leaving maintenance")
                self.at = core4.util.now()
                for step in self.plan:
                    interval = timedelta(seconds=step["interval"])
                    if step["next"] <= self.at:
                        self.logger.debug("enter [%s] at cycle [%s]",
                                          step["name"], self.cycle["total"])
                        step["call"]()
                        self.logger.debug("exit [%s] at cycle [%s]",
                                          step["name"], self.cycle["total"])
                        step["next"] = self.at + interval
            # create some idle time
            time.sleep(self.wait_time)

    def work_jobs(self):
        doc = self.get_next_job()
        if doc is None:
            return
        if not self.queue.lock_job(self.identifier, doc["_id"]):
            return
        try:
            job = self.queue.job_factory(doc["name"]).deserialise(**doc)
        except:
            # very early exception, so fail hard
            exc_info = sys.exc_info()
            update = {
                "state": core4.queue.job.STATE_ERROR,
                "started_at": self.at,
                "last_error": {
                    "exception": repr(exc_info[1]),
                    "traceback": traceback.format_exception(*exc_info),
                }
            }
            ret = self.config.sys.queue.update_one(
                filter={"_id": doc["_id"]},
                update={"$set": update})
            if ret.raw_result["n"] != 1:
                raise RuntimeError(
                    "failed to update job [{}] state [%s]".format(
                        doc["_id"], core4.queue.job.STATE_FAILED))
            return
        if job.inactive_at and job.inactive_at <= self.at:
            self.queue.inactivate_job(job)
            self.queue.unlock_job(job._id)
        else:
            self.start_job(job)

    def start_job(self, job):
        job.logger.info("start execution")
        at = core4.util.mongo_now()
        update = {
            "state": core4.queue.job.STATE_RUNNING,
            "started_at": at,
            "query_at": None,
            "locked": {
                "at": self.at,
                "heartbeat": self.at,
                "hostname": self.hostname,
                "pid": None,
                "progress_value": None,
                "progress": None,
                "worker": self.identifier,
                "username": None
            }
        }
        if job.inactive_at is None:
            update["inactive_at"] = at + timedelta(
                seconds=job.defer_max)
            self.logger.debug("set inactive_at [%s]", update["inactive_at"])
        # if job.wall_at is None:
        #     if job.wall_time is not None:
        #         update["wall_at"] = at + timedelta(
        #             seconds=job.wall_time)
        #         self.logger.debug("set wall_at [%s]", update["wall_at"])
        ret = self.config.sys.queue.update_one(
            filter={"_id": job._id}, update={"$set": update})
        if ret.raw_result["n"] != 1:
            raise RuntimeError(
                "failed to update job [{}] state [starting]".format(job._id))
        executable = job.python or sys.executable
        proc = subprocess.Popen(
            [
                executable,
                "-c", "from core4.queue.process import start; start()"
            ],
            env=os.environ,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE
        )
        ret = self.config.sys.queue.update_one(
            filter={
                "_id": job._id
            },
            update={
                "$set": {
                    "locked.pid": proc.pid
                }
            }
        )
        if ret.raw_result["n"] != 1:
            raise RuntimeError(
                "failed to update job [{}] pid [{}]".format(
                    job._id, proc.pid))
        job_id = str(job._id).encode("utf-8")
        proc.stdin.write(bytes(job_id))
        proc.stdin.close()
        self.logger.debug("successfully launched job [%s] at [%s]",
                          job._id, at)

    def get_next_job(self):
        query = [
            {'locked': None},
            {'attempts_left': {'$gt': 0}},
            {'$or': [
                {'state': s} for s in [
                    core4.queue.job.STATE_PENDING,
                    core4.queue.job.STATE_FAILED,
                    core4.queue.job.STATE_DEFERRED]]
            },
            {'$or': [{'worker': self.identifier},
                     {'worker': None}]},
            {'removed_at': None},
            {'killed_at': None},
            {'$or': [{'query_at': {'$lte': self.at}},
                     {'query_at': None}]},
        ]
        order = [
            ('force', pymongo.DESCENDING),
            ('priority', pymongo.DESCENDING),
            ('_id', pymongo.ASCENDING)
        ]
        if self.offset:
            cur2 = self.config.sys.queue.find(
                filter={'$and': query + [{"_id": {"$lte": self.offset}}]},
                sort=order)
            query.append({'_id': {'$gt': self.offset}})
        else:
            cur2 = None
        cur1 = self.config.sys.queue.find(
            filter={'$and': query}, sort=order)

        try:
            data = cur1.next()
        except StopIteration:
            data = None
        if cur2 is not None:
            try:
                data2 = cur2.next()
            except StopIteration:
                data2 = None
        else:
            data2 = None
        if data is None:
            if data2 is None:
                self.offset = None
                return None
            self.logger.debug(
                "next job from top chunk [%s]", data2["_id"])
            data = data2
        else:
            self.logger.debug(
                "next job from bottom chunk [%s]", data["_id"])
            if data2 is not None and data2["priority"] > data["priority"]:
                data = data2
                self.logger.debug(
                    "next job from prioritised top chunk [%s]",
                    data["_id"])
        self.offset = data["_id"]
        return data

    def remove_jobs(self):
        cur = self.config.sys.queue.find(
            {"removed_at": {"$ne": None}}
        )
        for doc in cur:
            if self.queue.lock_job(self.identifier, doc["_id"]):
                if self.queue.journal(doc):
                    ret = self.config.sys.queue.delete_one({"_id": doc["_id"]})
                    if ret.raw_result["n"] != 1:
                        raise RuntimeError(
                            "failed to remove job [{}]".format(doc["_id"]))
                    self.logger.info(
                        "successfully journaled and removed job [%s]",
                        doc["_id"])
                        # note: we will not unlock the job to prevent race
                        # conditions with other workds; this will be settled
                        # with .cleanup
                    continue
                self.logger.error(
                    "failed to journal and remove job [%s]", doc["_id"])

    def flag_jobs(self):
        cur = self.config.sys.queue.find(
            {
                "state": core4.queue.job.STATE_RUNNING,
                "locked.worker": self.identifier
            },
            projection=[
                "_id", "wall_time", "wall_at", "zombie_time",  "zombie_at",
                "started_at", "locked.heartbeat", "locked.pid", "killed_at"
            ]
        )
        for doc in cur:
            self.flag_nonstop(doc)
            self.flag_zombie(doc)
            self.check_pid(doc)
            self.kill_pid(doc)

    def flag_nonstop(self, doc):
        if doc["wall_time"] and not doc["wall_at"]:
            if doc["started_at"] < (self.at
                                    - timedelta(seconds=doc["wall_time"])):
                ret = self.config.sys.queue.update_one(
                    filter={
                        "_id": doc["_id"]
                    },
                    update={"$set": {"wall_at": core4.util.mongo_now()}})
                if ret.raw_result["n"] == 1:
                    self.logger.warning(
                        "successfully set non-stop job [%s]", doc["_id"])

    def flag_zombie(self, doc):
        if not doc["zombie_at"]:
            if doc["locked"]["heartbeat"] < (self.at
                                    - timedelta(seconds=doc["zombie_time"])):
                ret = self.config.sys.queue.update_one(
                    filter={
                        "_id": doc["_id"]
                    },
                    update={"$set": {"zombie_at": core4.util.mongo_now()}})
                if ret.raw_result["n"] == 1:
                    self.logger.warning(
                        "successfully set zombie job [%s]", doc["_id"])

    def pid_exists(self, doc):
        proc = None
        if doc["locked"] and doc["locked"]["pid"]:
            if psutil.pid_exists(doc["locked"]["pid"]):
                proc = psutil.Process(doc["locked"]["pid"])
                if proc.status() not in (psutil.STATUS_DEAD,
                                         psutil.STATUS_ZOMBIE):
                    return (True, proc)
        return (False, proc)

    def check_pid(self, doc):
        (found, proc) = self.pid_exists(doc)
        if not found and proc:
            self.logger.critical("pid [%s] not exists, killing",
                                 doc["locked"]["pid"])
            job = self.queue.load_job(doc["_id"])
            self.queue.set_killed(job)
            self.queue.unlock_job(job._id)


    def kill_pid(self, doc):
        if doc["killed_at"]:
            (found, proc) = self.pid_exists(doc)
            if found and proc:
                proc.kill()
                job = self.queue.load_job(doc["_id"])
                self.queue.set_killed(job)
                self.queue.unlock_job(job._id)

    def collect_stats(self):
        pass

    def shutdown(self):
        self.enter_phase("shutdown")

    def execute(self):
        pass

    def save_job(self):
        pass

    def load_job(self):
        pass
