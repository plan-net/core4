#This Source Code Form is subject to the terms of the Mozilla Public
#License, v. 2.0. If a copy of the MPL was not distributed with this
#file, You can obtain one at https://mozilla.org/MPL/2.0/.

from core4.config.main import CoreConfig, STANDARD_CONFIG
from core4.config.map import ConfigMap


class TestConfig(CoreConfig):

    cache = False

    def __init__(self, project_name=None, project_dict=None, local_dict=None,
                 extra_dict=None):
        self._project_name = project_name
        self._project_dict = project_dict or {}
        self._local_dict = local_dict or {}
        self._extra_dict = extra_dict or {}

    def _load(self):
        if self._project_name:
            project = (self._project_name, self._project_dict)
        else:
            project = None
        return ConfigMap(self._parse(
            self._read_yaml(STANDARD_CONFIG),  # standard core.yaml
            project,  # (project name, dict)
            self._local_dict,  # local config
            self._extra_dict))  # extra project dict

