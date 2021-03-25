#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os

from bson.objectid import ObjectId
from tornado.web import StaticFileHandler, HTTPError

import core4
import core4.const
from core4.api.v1.request.main import CoreRequestHandler


class CoreAssetHandler(CoreRequestHandler, StaticFileHandler):
    """
    The static asset handler delivers assets based on
    :class:`.CoreRequestHandler` static folder settings and the specified
    core4 default static folder.

    To serve assets, the templates must use methods :meth:`.static_url` and
    :meth:`.default_static`. If :meth:`.static_url` addresses an URL with a
    leading slash (``/``), then the method translates the static asset
    request into ``/core4/api/v1/_asset/default/<rsc_id>/<path>``. If the path
    does *not* start with a leading slash, then :meth:`.static_url` translates
    the static asset request into
    ``/core4/api/v1/file/project/<rsc_id>/<path>``. Watch the ``default``
    versus ``project`` modifier in both URLs. Absolute paths address assets
    from project root directory. Relative paths address asset from the
    specified static folder of the handler.

    Default asset requests are delivered according to the global core4 static
    file settings as defined by config attribute ``api.default_static``

    .. note:: This handler is used internally by core4. Normally you do not
              use or inherit from this handler.
    """
    author = "mra"
    title = "Asset Handler"
    default_filename = "index.html"
    doc = "Technical endpoint to deliver assets."

    def __init__(self, *args, **kwargs):
        CoreRequestHandler.__init__(self, *args, **kwargs)
        StaticFileHandler.__init__(self, *args, **kwargs)

    async def prepare(self):
        """
        Parses the URL and sets the static asset ``.root`` and ``.path_args``
        accordingly. Furthermore this method verifies authorization and access
        permissions.
        """
        default_static = self.config.api.default_static
        if default_static and not default_static.startswith("/"):
            default_static = os.path.join(os.path.dirname(core4.__file__),
                                          default_static)
        prefix = self.application.container.get_root(core4.const.ASSET_URL)
        parts = self.request.path[len(prefix) + 1:].split("/")
        mode = parts[0]
        rsc_id = parts[1]
        path = "/".join(parts[2:])
        if mode in ("default", "project"):
            if mode == "default":
                root = default_static
            else:
                handler = self.application.lookup[rsc_id]["handler"]
                if path.startswith("/"):
                    root = handler.target.project_path()
                    path = path[1:]
                else:
                    root = handler.target.set_path(
                        "static_path", self.application.container,
                        **handler.target_kwargs)
            self.root = root
            self.path_args = [path]
            full_path = os.path.join(self.root, self.path_args[0])
            if not os.path.exists(full_path):
                self.logger.error(
                    "static file not found [%s]", full_path)
        self.identifier = ObjectId()
        await self.prepare_protection()

    async def enter(self):
        raise HTTPError(400, "You cannot directly enter this endpoint.")
