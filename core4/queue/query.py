#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
This module delivers various MongoDB support methods retrieving information
about collections ``sys.queue``, ``sys.journal``, ``sys.stdout`` and
``sys.worker``. The main class :class:`QueryMixin` is to be mixed into a class
based on :class:`.CoreBase`.
"""

import datetime
from collections import OrderedDict

import core4.util.node


class QueryMixin:
    """
    Retrieves core4 runtime information by querying collections ``sys.queue``,
    ``sys.journal``, ``sys.stdout`` and ``sys.worker``.
    """

    def get_daemon(self, **kwargs):
        """
        Retrieves information about all daemons alive. This includes

        * ``_id`` - the identifier of the daemon
        * ``loop`` - the date/time when the daemon entered looping in UTC
        * ``loop_time`` - the timedelta of the daemon looping
        * ``heartbeat`` - the timedelta of the last heartbeat
        * ``kind`` - worker or scheduler

        .. note:: Daemons are considered alive, if their heartbeat is not older
                  then current date/time (all in UTC) plus the alive timeout.
                  The alive timeout can be configured by config section
                  ``alive.timeout``.

        :param kwargs: query filter
        :return: dict
        """
        cur = self.config.sys.worker.aggregate(self.pipeline_daemon(**kwargs))
        data = []
        for doc in cur:
            if doc["heartbeat"]:
                doc["heartbeat"] = (core4.util.node.mongo_now() -
                                    doc["heartbeat"].replace(microsecond=0))
            if doc.get("loop", None):
                doc["loop_time"] = (core4.util.node.mongo_now() -
                                    doc["loop"].replace(microsecond=0))
            else:
                doc["loop_time"] = None
                doc["loop"] = None
            data.append(doc)
        return data

    async def get_daemon_async(self):
        """
        Asynchronous version of :meth:`get_daemon`. Returns ``hearbeat`` and
        ``loop_time`` in total seconds instead of :class:`datetime.timedelta`.
        """
        cur = self.config.sys.worker.aggregate(self.pipeline_daemon())
        data = []

        def delta2sec(t):
            return (core4.util.node.mongo_now()
                    - t.replace(microsecond=0)).total_seconds()

        async for doc in cur:
            if doc["heartbeat"]:
                doc["heartbeat"] = delta2sec(doc["heartbeat"])
            if doc.get("loop", None):
                doc["loop_time"] = delta2sec(doc["loop"])
            else:
                doc["loop_time"] = None
                doc["loop"] = None
            data.append(doc)
        return data

    def pipeline_daemon(self, **kwargs):
        """
        Delivers aggregation pipeline of :meth:`get_daemon` and
        :meth:`get_daemon_async`.

        :param kwargs: optional aggregation match criteria
        :return: list of MongoDB aggregation pipeline statements
        """
        timeout = self.config.daemon.alive_timeout
        pipeline = []
        if kwargs:
            pipeline += [
                {
                    "$match": kwargs
                }
            ]

        pipeline += [
            {
                "$match": {
                    "heartbeat": {"$exists": True},
                    "phase.shutdown": None,
                    "$or": [
                        {"heartbeat": None},
                        {
                            "heartbeat": {
                                "$gte": core4.util.node.mongo_now() -
                                        datetime.timedelta(seconds=timeout)
                            }
                        }
                    ]
                },
            },
            {
                "$project": {
                    "heartbeat": 1,
                    "loop": "$phase.loop",
                    "kind": 1,
                    "pid": 1,
                    "hostname": 1,
                    "port": 1,
                    "protocol": 1
                }
            },
            {"$sort": {"kind": 1, "_id": 1}}
        ]
        return pipeline

    def get_queue_state(self):
        """
        Retrieves aggregated information about ``sys.queue`` state. This is

        * ``n`` - the number of jobs in the given state
        * ``state`` - job state
        * ``flags`` - job flags ``zombie``, ``wall``, ``removed`` and
          ``killed``
        * ``name`` - job :meth:`.qual_name``

        :return: dict
        """
        cur = self.config.sys.queue.aggregate(self.pipeline_queue_state())
        data = []
        for doc in cur:
            doc["flags"] = "".join(
                [k[0].upper() if doc[k] else "."
                 for k in ["zombie", "wall", "removed", "killed"]])
            data.append(doc)
        return data

    def pipeline_queue_state(self):
        """
        Delivers aggregation pipeline of :meth:`get_queue_state`.

        :return: list of MongoDB aggregation pipeline statements
        """

        sort_dict = OrderedDict()
        sort_dict['state'] = 1
        sort_dict['name'] = 1
        sort_dict['_id'] = -1
        return [
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
            {
                "$sort": sort_dict
            }
        ]

    def get_job_listing(self, **kwargs):
        """
        Returns the job listing filtered by {{kwargs}}. This is

        * ``_id`` (ObjectId)
        * ``attempts_left`` (int)
        * ``attempts`` (int)
        * ``started_at`` (datetime)
        * ``enqueued`` (dict)
        * ``priorirty`` (int)
        * ``args`` (dict)
        * ``killed_at`` (datetime)
        * ``removed_at`` (datetime)
        * ``zombie_at`` (datetime)
        * ``wall_at`` (datetime)
        * ``name`` (str)
        * ``state`` (str)
        * ``locked`` (dict)
        * ``prog`` (dict)

        :param kwargs: query filter
        :return: dict generator
        """
        return self.config.sys.queue.find(
            filter=kwargs,
            projection=self.project_job_listing(),
            sort=[('_id', 1)])

    def job_detail(self, _id):
        """
        full job details from ``sys.queue`` or ``sys.journal``.

        :param _id: :class:`bson.objectid.ObjectId`
        :return: dict
        """
        doc = self.config.sys.queue.find_one(
            filter={"_id": _id})
        if doc is None:
            doc = self.config.sys.journal.find_one(
                filter={"_id": _id})
            if doc is not None:
                doc["journaled"] = True
        return doc

    def project_job_listing(self):
        """
        Returns the ``sys.queue`` attributes to be projected in a job listing.

        :return: dict of attributes
        """
        return {
            '_id': 1,
            'attempts_left': 1,
            'attempts': 1,
            'trial': 1,
            'started_at': 1,
            'enqueued': 1,
            'priority': 1,
            'args': 1,
            'killed_at': 1,
            'removed_at': 1,
            'zombie_at': 1,
            'finished_at': 1,
            'runtime': 1,
            'wall_at': 1,
            'name': 1,
            'state': 1,
            'locked': 1,
            'prog': 1
        }

    def get_job_stdout(self, _id):
        """
        Returns the job STDOUT filtered.

        .. note:: The STDOUT of jobs have a time-to-live and is purged after
                  7 days. You can configure this TTL with config setting
                  ``worker.stdout.ttl``.

        :param _id: :class:`bson.object.ObjectId`
        :return: str
        """
        doc = self.config.sys.stdout.find_one({"_id": _id})
        if doc:
            return doc["stdout"]
        return None

    def pipeline_queue_count(self):
        """
        Returns the pipeline commands to count jobs in different states.

        :return: list of MongoDB pipeline commands
        """
        return [
            {
                '$match': {
                    'state': {'$ne': 'complete'}
                },
            },
            {
                '$project': {
                    "state": 1
                },
            },
            {
                '$group': {
                    '_id': {
                        'state': '$state'
                    },
                    'n': {'$sum': 1}
                }
            },
            {
                '$project': {
                    "state": "$_id.state",
                    "n": "$n",
                    "_id": 0,
                },
            }
        ]

    def get_queue_count(self):
        """
        Retrieves aggregated information about ``sys.queue`` state. This is

        * ``n`` - the number of jobs in the given state
        * ``state`` - job state
        * ``flags`` - job flags ``zombie``, ``wall``, ``removed`` and
          ``killed``

        :return: dict
        """
        cur = self.config.sys.queue.aggregate(self.pipeline_queue_count())
        data = list(cur)
        return dict([(s["state"], s["n"]) for s in data])
