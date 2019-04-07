#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# todo: documentation

import inspect
import os
import sys
from distutils import log

from setuptools import setup as _orig_setup

if sys.version_info < (3, 5):
    sys.exit('requires Python 3.5 or higher')

# ensure pip >= 18.1
import pip

if tuple([int(i) for i in pip.__version__.split(".")]) < (18, 1):
    sys.exit("requires pip version 18.1 or higher, "
             "Upgrade with `pip install --upgrade pip`")


# WEBDIST = os.path.join(os.path.dirname(sys.executable), "..", "webapps.dist")
#
# def write_webdist(webapps):
#     with open(WEBDIST, "w", encoding="utf-8") as fh:
#         json.dump(webapps, fh, indent=2)
#
#
# def read_webdist():
#     if os.path.exists(WEBDIST):
#         with open(WEBDIST, "r", encoding="utf-8") as fh:
#             return json.load(fh)
#     return {}
#
#
def read_install_requires(folder):
    source = os.path.abspath(os.path.join(folder, "install_requires.txt"))
    if os.path.exists(source):
        with open(source, "r", encoding="utf-8") as fh:
            return [pkg.strip() for pkg in fh.readlines() if pkg.strip()]
    return []


#
#
# class BuildCore4Web(build_py):
#
#     def print(self, msg):
#         self.announce("core4.setup: " + msg, level=log.INFO)
#
#     def run(self):
#         self.print("setup from [{}]".format(
#             sys.modules[self.__module__].__file__))
#         webapps = {}
#         for package in self.packages:
#             package_dir = os.path.abspath(self.get_package_dir(package))
#             for (path, directories, filenames) in os.walk(package_dir):
#                 for filename in filenames:
#                     if filen
#                     ame == "package.json":
#                         with open(os.path.join(path, filename), 'r',
#                                   encoding="utf-8") as fh:
#                             package_json = json.load(fh)
#                         if "core4" in package_json:
#                             command = package_json["core4"].get(
#                                 "build_command", [])
#                             dist = package_json["core4"].get("dist", None)
#                             if dist:
#                                 self.print(
#                                     "package_dir: {}".format(package_dir))
#                                 self.print("dist: {}".format(dist))
#                                 dist_path = os.path.join(
#                                     path[len(package_dir) + 1:], dist)
#                                 self.print("dist_path: {}".format(dist_path))
#                                 if path not in webapps:
#                                     self.print("found [{}] in [{}]".format(
#                                         dist_path, package))
#                                     webapps[path] = {
#                                         "package": package,
#                                         # "package_dir": package_dir,
#                                         "dist_path": dist_path,
#                                         "dist": dist,
#                                         "command": command
#                                     }
#         write_webdist(webapps)
#
#

# class BuildCore4Web(build_py):
#
#     def print(self, msg):
#         self.announce("core4.setup: " + msg, level=log.INFO)
#
#     def run(self):
#         self.print("setup from [{}]".format(
#             sys.modules[self.__module__].__file__))
#         build_py.run(self)
# #         start_dir = os.path.abspath(os.curdir)
# #         webapps = read_webdist()
# #         for pkg_path, meta in webapps.items():
# #             self.print("package [{}] build in [{}]".format(meta["package"],
# #                                                            pkg_path))
# #             os.chdir(pkg_path)
# #             if os.path.exists(meta["dist"]):
# #                 self.print("clean [{}]".format(meta["dist"]))
# #                 shutil.rmtree(meta["dist"])
# #             for part in meta["command"]:
# #                 check_call(part, shell=True)
# #             os.chdir(start_dir)
# #             pkg_name = meta["package"]
# #             if pkg_name not in self.package_data:
# #                 self.package_data[pkg_name] = []
# #             self.package_data[pkg_name].append(meta["dist_path"] + "/*")
# #             self.package_data[pkg_name].append(meta["dist_path"] + "/**/*")
# #             self.print("sourcing [{}]".format(meta["dist_path"]))
# #         os.chdir(start_dir)
# #         build_py.finalize_options(self)
# #         self.print("package_data: {}".format(self.package_data))


from setuptools.command.install import install
from distutils.cmd import Command

class CommandMixin(object):

    def print(self, msg):
        self.announce("core4.setup: " + msg, level=log.INFO)


class InstallCommand(install, CommandMixin):

    def run(self):
        self.print("setup from [{}]".format(
            sys.modules[self.__module__].__file__))
        self.print("this [{}]".format(self.__class__.__name__))
        super().run()


class BuildWebCommand(Command, CommandMixin):
    description = "custom clean command that forcefully removes dist/build directories"
    user_options = []

    def initialize_options(self):
        self.root = None

    def finalize_options(self):
        pass

    def run(self):
        self.print("setup from [{}]".format(
            sys.modules[self.__module__].__file__))
        self.print("this [{}]".format(self.__class__.__name__))
        self.print("root: [{}]".format(self.root))
        self.print("*"*120)
        for pkg in self.distribution.packages:
            self.print("package: {}".format(pkg))


def setup(*args, **kwargs):
    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])
    caller_dir = os.path.dirname(os.path.abspath(module.__file__))
    kwargs.setdefault("install_requires", [])
    kwargs["install_requires"] += read_install_requires(caller_dir)
    kwargs.setdefault("package_data", {})
    kwargs["package_data"].setdefault("", [])
    kwargs.setdefault("zip_safe", False)
    kwargs.setdefault("include_package_data", True)
    kwargs["package_data"][""] += [kwargs["name"] + ".yaml"]
    kwargs["cmdclass"] = {
        "install": InstallCommand,
        "web": BuildWebCommand,
    }
    kwargs["options"] = {
        "web": {
            "root": caller_dir
        }
    }
    _orig_setup(*args, **kwargs)
