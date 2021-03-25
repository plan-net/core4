#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
core4 :class:`.CoreStaticFileHandler`, based on :mod:`tornado`
:class:`StaticFileHandler <tornado.web.StaticFileHandler>` and
:class:`.CoreBaseHandler`.

"""
from core4.api.v1.request.main import CoreRequestHandler


class CoreLinkHandler(CoreRequestHandler):

    """
    Visit {{ enter_url }}
    """
    target = "blank"
    
    def get(self):
        """
        Redirect to the specified URL.
        """
        return self.redirect(self.enter_url)
