#
# Copyright 2019 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""

Start the server with::
    $ python core4/api/v1/server.widget.py
"""


from core4.api.v1.application import CoreApiContainer
from core4.api.v1.request.standard.event import EventWatch
from core4.api.v1.request.standard.event import QueueWatch
from core4.api.v1.tool.functool import serve
from core4.api.v1.request.static import CoreStaticFileHandler

class CoreApiServer(CoreApiContainer):
    """
    Default :class:`.CoreApiContainer` serving the standard core4 endpoints
    at ``/core4/api/v1``.
    """
    root = "/core4/api/v1"
    rules = [
        ("/widgets", CoreStaticFileHandler, {"path": "../webapps/widgets/dist", "protected": True, "title": "core widgets"})
    ]


if __name__ == '__main__':
    serve(CoreApiServer, routing="localhost:5001", address="0.0.0.0")

