#This Source Code Form is subject to the terms of the Mozilla Public
#License, v. 2.0. If a copy of the MPL was not distributed with this
#file, You can obtain one at https://mozilla.org/MPL/2.0/.

from yaml.loader import SafeLoader

from core4.config.main import CoreConfig
from core4.config.tag import ConnectTag

SafeLoader.add_constructor('!connect', ConnectTag.from_yaml)
