from core4.config.main import CoreConfig, STANDARD_CONFIG
from core4.config.map import ConfigMap


class TestConfig(CoreConfig):

    def __init__(self, plugin_name=None, plugin_dict=None, local_dict=None,
                 extra_dict=None):
        self._plugin_name = plugin_name
        self._plugin_dict = plugin_dict or {}
        self._local_dict = local_dict or {}
        self._extra_dict = extra_dict or {}

    def _load(self):
        if self._plugin_name:
            plugin = (self._plugin_name, self._plugin_dict)
        else:
            plugin = None
        return ConfigMap(self._parse(
            self._read_yaml(STANDARD_CONFIG),  # standard core.yaml
            plugin,  # (plugin name, dict)
            self._local_dict,  # local config
            self._extra_dict))  # extra plugin dict

