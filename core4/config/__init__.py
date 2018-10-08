from yaml.loader import SafeLoader

from core4.config.main import CoreConfig
from core4.config.tag import ConnectTag

SafeLoader.add_constructor('!connect', ConnectTag.from_yaml)
