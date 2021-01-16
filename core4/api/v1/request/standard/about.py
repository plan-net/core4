#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Implements core4os standard :class:`.AboutHandler`.
"""

from core4.api.v1.request.main import CoreRequestHandler
import core4
from core4.api.v1.request.store import StoreHandler
from core4.queue.query import QueryMixin


class AboutHandler(CoreRequestHandler, QueryMixin):
    """
    Information about core4os operating platform
    """
    author = "mra"
    title = "About core4os"
    subtitle = "core4os Information"
    tag = ["cooperations"]
    icon = "mdi-information"

    async def get(self):
        """
        Methods:
            GET /core4/api/v1/about -

        Parameters:
            None

        Returns:
            data element or rendered ``./about.html`` with

            - worker (int): active workers
            - app (int): active application servers
            - scheduler (int): active schedulers
            - jobs (int): active jobs
            - handlers (int): ative web service handlers
            - version (str): core4os release number
            - timestamp (datetime): core4os release date/time
            - contact (str): email contact

        Raises:
            401: Unauthorized

        Examples:
            >>> from requests import get
            >>> rv = get("http://localhost:5001/core4/api/v1/about")
            >>> rv.json()
        """
        store = StoreHandler(self.application, self.request)
        s = await store.load(self.user)
        daemon = await self.get_daemon_async()
        worker = [d for d in daemon if d["kind"] == "worker"]
        app = [d for d in daemon if d["kind"] == "app"]
        scheduler = [d for d in daemon if d["kind"] == "scheduler"]
        query = {"updated_at": {"$ne": None}, "valid": True}
        job = await self.config.sys.job.count_documents(query)
        project = await self.config.sys.job.distinct("project", query)
        handler = await self.application.container.get_handler()
        project += [h["project"] for h in handler]
        data = {
            "worker": len(worker),
            "app": len(app),
            "scheduler": len(scheduler),
            "jobs": job,
            "projects": len(list(set(project))),
            "handlers": len(handler),
            "version": "4." + core4.__version__,
            "timestamp": core4.__built__,
            "contact": s["doc"]["contact"]
        }
        self.render("template/about.html", **data)
