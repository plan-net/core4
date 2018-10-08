import datetime
import pandas as pd

import core4.util


class QueryMixin:

    def get_worker(self):
        timeout = self.config.worker.alive_timeout
        cur = self.config.sys.worker.aggregate([
            {
                "$match": {
                    "heartbeat": {"$exists": True},
                    "$or": [
                        {"heartbeat": None},
                        {
                            "heartbeat": {
                                "$gte": core4.util.mongo_now() -
                                        datetime.timedelta(seconds=timeout)
                            }
                        }
                    ]
                },
            },
            {
                "$project": {
                    "heartbeat": 1,
                    "looping": "$phase.loop"
                }
            },
            {"$sort": {"_id": 1}}
        ])
        data = list(cur)
        df = pd.DataFrame(data)
        if df.empty:
            return None
        df["heartbeat"] = core4.util.now() - df.heartbeat
        df["looping"] = core4.util.mongo_now() - df.looping
        return df

    def get_queue_state(self):
        cur = self.config.sys.queue.aggregate([
            {
                '$match': {
                    'state': {'$ne': 'complete'}
                },
            },
            {
                '$project': {
                    "name": 1,
                    "state": 1,
                    "zombie": {"$ne": ["$zombie_at", None]},
                    "wall": {"$ne": ["$wall_at", None]},
                    "removed": {"$ne": ["$removed_at", None]},
                    "killed": {"$ne": ["$killed_at", None]}
                },
            },
            {
                '$group': {
                    '_id': {
                        'name': '$name',
                        'state': '$state',
                        'zombie': '$zombie',
                        'wall': '$wall',
                        'removed': '$removed',
                        'killed': '$killed',
                    },
                    'n': {'$sum': 1}
                }
            },
            {
                '$project': {
                    "name": "$_id.name",
                    "state": "$_id.state",
                    "zombie": "$_id.zombie",
                    "wall": "$_id.wall",
                    "removed": "$_id.removed",
                    "killed": "$_id.killed",
                    "n": "$n",
                    "_id": 0,
                },
            },
        ])
        data = list(cur)
        df = pd.DataFrame(data)
        df["flags"] = df.apply(lambda r: "".join(
            [k[0].upper() if r[k] else "." for k in
             ["zombie", "wall", "removed", "killed"]]), axis=1)
        return df[["n", "state", "flags", "name"]]


"""
cur = q.config.sys.queue.find(filter={'state': "running"},
                              projection={'_id': 1,
                                          'attempts_left': 1,
                                          'attempts': 1,
                                          'started_at': 1,
                                          'enqueued': 1,
                                          'priority': 1,
                                          'args': 1,
                                          'killed_at': 1,
                                          'zombie_at': 1,
                                          'wall_at': 1,
                                          'name': 1,
                                          'locked': 1},
                              sort=[('_id', 1)])
import core4.util

now = core4.util.now().replace(microsecond=0)

header = ("{:24s} "
          "{:16s} "
          "{:3s} "
          "{:5s} "
          "{:8s} "
          "{:8s} "
          "{:3s} "
          "{:6s} "
          "{:s} "
          "".format(
    "_id",
    "worker",
    "prio",
    "atmpt",
    "age",
    "runtime",
    "flg",
    "user",
    "name"
))
for line in data:
    print("{_id:s} "
          "{worker:16.16s} "
          "{priority:04d} "
          "{attempt:02d}/{attempts:02d} "
          "{age:>8s} "
          "{runtime:>8s} "
          "{killed:1s}{walled:1s}{zombie:1s} "
          "{by:6.6s} "
          "{name:s} "
          "".format(
        worker=line["locked"]["worker"],
        _id=str(line["_id"]),
        name=line["name"],
        by=line["enqueued"]["username"],
        attempt=line["attempts_left"] - line["attempts"] + 1,
        attempts=line["attempts"],
        age=str(now - line["enqueued"]["at"]),
        runtime=str(now - line["started_at"]),
        priority=line["priority"],
        killed="K" if line["killed_at"] else ".",
        walled="K" if line["wall_at"] else ".",
        zombie="K" if line["zombie_at"] else ".",
    ))

"""
