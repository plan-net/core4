#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
This module carries several global constants relevant to multiple core4
modules.
"""

CORE4 = "core4"
PREFIX = "project"  # project logger beneath "core4.project"
COP = "cop"
INFO_URL = "/_info"
ENTER_MODE = "enter"
CARD_MODE = "card"
HELP_MODE = "help"
ASSET_URL = "_asset"
CARD_METHOD = "XCARD"
HELP_METHOD = "XHELP"
QUICK_HELP_METHOD = "XHELP2"
ENTER_METHOD = "XENTER"

VENV = ".venv"
REPOSITORY = ".repos"
VENV_PYTHON = VENV + "/bin/python"
VENV_PIP = VENV + "/bin/pip3"

QUEUE_CHANNEL = "queue"
DEFAULT_CHANNEL = "system"
MESSAGE_CHANNEL = "message"

CORE4_REPOSITORY = "git+https://github.com/plan-net/core4.git"