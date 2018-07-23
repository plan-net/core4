# -*- coding: utf-8 -*-

CORE4_PREFIX = "core4"  # top logger "core4"
ACCOUNT_PREFIX = "account"  # plugin logger beneath "core4.account"


from core4.logger.mixin import CoreLoggerMixin
from core4.logger.adapter import CoreLoggingAdapter
