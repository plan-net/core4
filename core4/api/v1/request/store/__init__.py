#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os.path

from core4.base.main import CoreBase


class CoreStore(CoreBase):
    concurr = True

    @classmethod
    async def load(cls, user):
        return await cls().load_by_user(user)

    async def load_by_user(self, user):
        xpath = None
        if user is not None:
            for app in await user.casc_perm():
                if app.startswith("app://store"):
                    xpath = app[len("app://store"):]
                    break
        if xpath is None:
            xpath = "/"
        xpath = self.make_path(xpath)
        return await self.parse(xpath)

    async def parse(self, xpath):
        parts = xpath.split("/")
        if xpath == "/":
            parents = [xpath]
        else:
            parents = []
        while xpath != "/":
            parent = "/".join(parts)
            if not parent:
                parent = "/"
            parents.append(parent)
            parts.pop(-1)
            if not parts:
                break
        parents = list(reversed(parents))
        doc = self.raw_config.store.default
        for parent in parents:
            pdoc = await self.config.sys.store.find_one({"_id": parent})
            if pdoc is not None:
                doc.update(pdoc)
        return {"parents": parents, "doc": doc}

    def make_path(self, xpath):
        if xpath is None:
            return "/"
        if not xpath.startswith("/"):
            xpath = "/" + xpath
        return os.path.normpath(xpath)


