#This Source Code Form is subject to the terms of the Mozilla Public
#License, v. 2.0. If a copy of the MPL was not distributed with this
#file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Implements the logging adapter :class:`CoreLoggingAdapter`.
"""

import logging.config


class CoreLoggingAdapter(logging.LoggerAdapter):
    """
    This adapter passes the object to logging.
    """

    def process(self, msg, kwargs):
        kwargs.setdefault("extra", {}).update({"obj": self.extra})
        return msg, kwargs
