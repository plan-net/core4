import logging
import os

import core4.util


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
        record.username = core4.util.get_username()
        record.hostname = core4.util.get_hostname()
        try:
            if not hasattr(record, "identifier"):
                record.identifier = record.obj.identifier
        except:
            record.identifier = None
        try:
            record.qual_name = record.obj.qual_name(short=True)
        except:
            record.qual_name = "basename:" + os.path.basename(record.pathname)
        return 1
