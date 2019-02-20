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
CORE4_API = "/core4/api/v1"
INFO_URL = CORE4_API + "/info"
ENTER_URL = CORE4_API + "/enter"
CARD_URL = INFO_URL + "/card"
HELP_URL = INFO_URL
FILE_URL = CORE4_API + "/file"
SETTING_URL = CORE4_API + "/setting"
CARD_METHOD = "XCARD"
HELP_METHOD = "XHELP"
ENTER_METHOD = "XENTER"

VENV = ".venv"
REPOSITORY = ".repos"
VENV_PYTHON = VENV + "/bin/python"
VENV_PIP = VENV + "/bin/pip3"

