# -*- coding: utf-8 -*-

from core4.config.directive import ConnectTag
from core4.config.main import CoreConfig
from yaml.loader import SafeLoader


SafeLoader.add_constructor('!connect', ConnectTag.from_yaml)

