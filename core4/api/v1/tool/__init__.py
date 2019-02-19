#This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Helper tools :meth:`.serve`` and :meth:`.serve_all` with the underlying
:class:`.CoreApiServerTool`.
"""

if __name__ == '__main__':
    # from core4.service.introspect import CoreIntrospector
    # intro = CoreIntrospector()
    # for pro in intro.iter_project():
    #     print(pro)
    serve_all(filter=["project.api",  # "core4",
                      "example"])  # , name=sys.argv[1], port=int(sys.argv[2]))
