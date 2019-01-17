import logging
import os

import core4.util
import core4.util.node


class CoreLoggingFilter(logging.Filter):
    """
    This filter adds the following properties to the
    :class:`logging.LogRecord`:

    * username
    * hostname
    * identifier
    * qual_name
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
