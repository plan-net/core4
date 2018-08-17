# -*- coding: utf-8 -*-

from yaml.loader import SafeLoader

from core4.config.tag import ConnectTag
from core4.config.main import CoreConfig

SafeLoader.add_constructor('!connect', ConnectTag.from_yaml)

