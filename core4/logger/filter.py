#
#Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
#This Source Code Form is subject to the terms of the Mozilla Public
#License, v. 2.0. If a copy of the MPL was not distributed with this
#file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
:class:`CoreLoggingFilter` adds several properties to
:class:`logging.LogRecord`.
"""
import logging
import os

import core4.util.node


class CoreLoggingFilter(logging.Filter):
    """
    This filter adds the following properties to the
    :class:`logging.LogRecord`:

    * username
    * hostname
    * identifier
    * qual_name
    * epoch
    """

    def filter(self, record):
        record.username = core4.util.node.get_username()
        record.hostname = core4.util.node.get_hostname()
        try:
            if not hasattr(record, "identifier"):
                record.identifier = record.obj.identifier
        except:
            record.identifier = None
        try:
            record.qual_name = record.obj.qual_name(short=True)
        except:
            record.qual_name = "basename:" + os.path.basename(record.pathname)
        record.epoch = core4.util.node.now().timestamp()
        return 1
