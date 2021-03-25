#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from core4.api.v1.request.main import CoreRequestHandler


class DefaultHandler(CoreRequestHandler):
    title = "default handler"
    author = "mra"
    protected = False

    """
    Handles all non-existing endpoints throwing ``404`` - ``Not Found``.
    """

    def initialize(self, *args, status_code=404, **kwargs):
        self.set_status(status_code)

    def check_xsrf_cookie(self):
        pass

    def get(self, *args, **kwargs):
        self.write_error(self.get_status())
