#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from tornado.ioloop import IOLoop
from tornado.web import HTTPError

from core4.api.v1.request.main import CoreRequestHandler


class KillHandler(CoreRequestHandler):
    title = "app server kill handler"
    author = "mra"
    protected = True

    async def post(self):
        if not await self.user.is_admin():
            raise HTTPError(403, "cops only")
        self.reply("going down now")
        self.logger.warning("stop IOLoop now")
        from core4.api.v1.tool.serve import CoreApiServerTool
        CoreApiServerTool.stop()
