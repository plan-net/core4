#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# todo: documentation

import inspect
import json
import os
import pickle
import sys
from distutils import log
from subprocess import check_call

import shutil
from setuptools import setup as _orig_setup
from setuptools.command.build_py import build_py

if sys.version_info < (3, 5):
    sys.exit('requires Python 3.5 or higher')

# ensure pip >= 18.1
import pip

if tuple([int(i) for i in pip.__version__.split(".")]) < (18, 1):
    sys.exit("requires pip version 18.1 or higher, "
             "Upgrade with `pip install --upgrade pip`")


def read_install_requires(folder):
    source = os.path.abspath(os.path.join(folder, "install_requires.txt"))
    if os.path.exists(source):
        with open(source, "r", encoding="utf-8") as fh:
            return [pkg.strip() for pkg in fh.readlines() if pkg.strip()]
    return []


class BuildCore4Web(build_py):

    def print(self, msg):
        self.announce("core4.setup: " + msg, level=log.INFO)

    def run(self):
        webapps = []
        for package in self.packages:
            package_dir = os.path.abspath(self.get_package_dir(package))
            for (path, directories, filenames) in os.walk(package_dir):
                for filename in filenames:
                    if filename == "package.json":
                        with open(os.path.join(path, filename), 'r',
                                  encoding="utf-8") as fh:
                            package_json = json.load(fh)
                        if "core4" in package_json:
                            command = package_json["core4"].get(
                                "build_command", [])
                            dist = package_json["core4"].get("dist", None)
                            dist_path = os.path.join(
                                path[len(package_dir) + 1:],
                                dist)
                            if dist:
                                self.print("found [{}] in [{}]".format(
                                    dist_path, package))
                                webapps.append({
                                    "package": package,
                                    "package_dir": package_dir,
                                    "build_path": path,
                                    "dist_path": dist_path,
                                    "dist": dist,
                                    "command": command
                                })
        webapps_file = os.path.join(os.path.dirname(sys.executable), "..",
                                    "webapps.dist")
        self.print("writing to [{}]".format(webapps_file))
        pickle.dump(webapps, open(webapps_file, "wb"))


class BuildCore4(build_py):

    def print(self, msg):
        self.announce("core4.setup: " + msg, level=log.INFO)

    def run(self):
        start_dir = os.path.abspath(os.curdir)
        webapps_file = os.path.join(os.path.dirname(sys.executable), "..",
                                    "webapps.dist")
        if os.path.exists(webapps_file):
            self.print("reading from [{}]".format(webapps_file))
            webapps = pickle.load(open(webapps_file, "rb"))
            for copy in webapps:
                self.print(
                    "build [{}] in [{}] build in [{}]".format(
                        copy["package"], copy["package_dir"],
                        copy["build_path"]))
                os.chdir(copy["package_dir"])
                os.chdir(copy["build_path"])
                if os.path.exists(copy["dist"]):
                    self.print("clean [{}]".format(copy["dist"]))
                    shutil.rmtree(copy["dist"])
                for part in copy["command"]:
                    check_call(part, shell=True)
                os.chdir(copy["dist"])
                if copy["package"] not in self.package_data:
                    self.package_data[copy["package"]] = []
                for (path, directories, filenames) in os.walk("."):
                    for filename in filenames:
                        relname = os.path.join(copy["dist_path"], path,
                                               filename)
                        self.print("adding [{}]".format(relname))
                        self.package_data[copy["package"]].append(relname)
        # self.print("final {}".format(self.package_data))
        os.chdir(start_dir)
        build_py.run(self)


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
        "build_py": BuildCore4,
        "build_web": BuildCore4Web,
    }
    _orig_setup(*args, **kwargs)
