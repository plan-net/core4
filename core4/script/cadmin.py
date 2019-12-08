#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
cadmin - core-4 build and deployment utililty.

Usage:
  cadmin install [--reset] [--web] [--home=HOME] [--build=APP...] REPOSITORY PROJECT
  cadmin upgrade [--test] [--force] [--reset] [--nobuild] [--home=HOME] [PROJECT...]
  cadmin dep-upgrade [--home=HOME] PACKAGE [PROJECT...]
  cadmin uninstall [--home=HOME] PROJECT...
  cadmin version [--home=HOME] [PROJECT...]
  cadmin build [--build=APP...]

Arguments:
  REPOSITORY  requirements specifier with VCS support (see pip documentation)
  PROJECT     project name

Options:
  --home=HOME         set core4 home directory, defaults to config.folder.home
  -r --reset          reset existing project root
  -f --force          force build and installation even if no changes
  -w --web            build and install web apps
  -b --build=APP      build and install web apps
  -d --dependency=DEP upgrade package dependency
  -e --nobuild        skip build and install of web apps
  -t --test           dry-run
  -h --help           show this screen
  -v --version        show version
"""

import datetime
import importlib
import json
import os
import re
import shutil
from subprocess import Popen, STDOUT, PIPE, DEVNULL

import core4.const
import setuptools
import sys
from core4.base.main import CoreBase
from docopt import docopt

LOGFILE = os.path.join(os.path.abspath("."), "cadmin.log")
CLONE = ".origin"
CONFIG = ".config"
VERSION_COMMAND = """
import {p}
import core4
print(", ".join([{p}.__version__, {p}.__built__, core4.__version__, 
                 core4.__built__]))
"""

if os.path.exists(LOGFILE):
    os.unlink(LOGFILE)

# ensure pip >= 18.1
import pip

#: minimum required pip version
PIP_VERSION = (18, 1)
if tuple([int(i) for i in pip.__version__.split(".")]) < PIP_VERSION:
    sys.exit("requires pip version 18.1 or higher, "
             "Upgrade with `pip install --upgrade pip`")


class InstallMixin:
    @staticmethod
    def print(msg):
        logfile = open(LOGFILE, "a", encoding="utf-8")
        logfile.write(msg + "\n")
        logfile.close()
        print(msg)


class WebBuilder(CoreBase, InstallMixin):

    def init_vars(self, root):
        self.root = os.path.abspath(root)
        self.venv = os.path.join(self.root, core4.const.VENV)
        self.pip = os.path.join(self.root, core4.const.VENV_PIP)
        self.python = os.path.join(self.root, core4.const.VENV_PYTHON)
        self.project_config = os.path.join(self.root, CONFIG)
        self.env = os.environ

    def build(self, filter):
        self.print("  build webapps in [{}]".format(self.root))
        for build in self.identify_webapp(self.root):
            if (filter == [] or build["name"] in filter):
                self.print("    build [{}]".format(build["base"]))
                self.clean_webapp(os.path.join(build["base"], build["dist"]))
                self.build_webapp(build["base"], build["command"])

    def clean_webapp(self, dist):
        if os.path.exists(dist):
            self.print("    clean [{}]".format(dist))
            shutil.rmtree(dist)

    def build_webapp(self, base, command):
        os.chdir(base)
        fh = open(LOGFILE, "a", encoding="utf-8")
        for cmd in command:
            self.print("    $ {}".format(cmd))
            proc = Popen(cmd, shell=True, env=self.env, stdout=PIPE,
                         stderr=STDOUT)
            for line in proc.stdout:
                line = line.decode("utf-8")
                fh.write(line)
                self.print("      {}".format(line.strip()))
        fh.close()
        os.chdir(self.root)

    def identify_webapp(self, folder):
        for path, directories, filenames in os.walk(folder):
            for directory in directories:
                pkg_json_file = os.path.join(path, directory, "package.json")
                if os.path.exists(pkg_json_file):
                    try:
                        pkg_json = json.load(
                            open(pkg_json_file, "r", encoding="utf-8"))
                        if "core4" in pkg_json:
                            command = pkg_json["core4"].get(
                                "build_command", None)
                            dist = pkg_json["core4"].get(
                                "dist", None)
                            if command is not None and dist is not None:
                                yield {
                                    "base": os.path.join(path, directory),
                                    "command": command,
                                    "dist": dist,
                                    "name": pkg_json.get("name", None)
                                }
                    except:
                        self.print("    failed to parse [{}]".format(
                            pkg_json_file))


class CoreInstaller(WebBuilder):

    def __init__(self, project, repository=None, reset=False, web=False,
                 home=None):
        super().__init__()
        self.project = project
        self.repository = repository
        self.reset = reset
        self.web = web
        self.install_requires = None
        self.home = home or self.config.folder.home
        root = os.path.join(self.home, self.project)
        self.clone = os.path.join(root, CLONE)
        self.init_vars(root)
        if "PYTHONPATH" in self.env:
            del self.env["PYTHONPATH"]

    def check_for_install(self):
        """
        Verify ``folder.home`` is defined, project does not exist,
        and no virtual environment exists, yet.
        """
        if self.home is None or not os.path.exists(self.home):
            raise SystemExit(
                "core4 config [folder.home] is None or not exists")
        if os.path.exists(self.root):
            raise SystemExit("project root [{}] exists".format(self.root))
        if os.path.exists(self.venv):
            raise SystemExit("virtual environment [{}] exists".format(
                self.venv))

    def check_for_upgrade(self):
        """
        Verify ``folder.home`` is defined, project does exists,
        and virtual environment exists.
        """
        if self.home is None or not os.path.exists(self.home):
            raise SystemExit("core4 config [folder.home] not set or None")
        if not os.path.exists(self.root):
            raise SystemExit("project root [{}] not found".format(
                self.root))
        if not os.path.exists(self.venv):
            raise SystemExit("virtual environment [{}] not found".format(
                self.venv))

    def install(self, filter=None):
        if self.reset:
            self.uninstall()
        self.check_for_install()
        self.print("installing [{}]".format(self.project))
        os.makedirs(self.root)
        os.chdir(self.root)

        self.print("  created project root [{}]".format(self.root))
        self.install_venv()
        self.upgrade_pip()
        if os.path.isdir(self.repository):
            self.clone = self.repository
        else:
            self.checkout()
        self.install_project()
        self.write_config()
        if self.web:
            self.build(filter)

    def write_config(self):
        data = {
            "repository": self.repository,
            "commit": self.get_local_commit(),
            "web": self.web,
            "install_requires": self.install_requires
        }
        json.dump(data, open(self.project_config, "w", encoding="utf-8"))

    def read_config(self):
        data = json.load(open(self.project_config, "r", encoding="utf-8"))
        return data

    def get_local_commit(self):
        os.chdir(self.clone)
        (out, _) = Popen(["git", "--no-pager", "log", "-n", "1",
                          "--pretty=format:%H"], env=self.env, stdout=PIPE,
                         stderr=DEVNULL).communicate()
        return out.decode("utf-8").strip()

    def get_commit_datetime(self, commit):
        os.chdir(self.clone)
        (out, _) = Popen(["git", "--no-pager", "log", "-n", "1",
                          "--pretty=format:%aD", commit], env=self.env,
                         stdout=PIPE, stderr=DEVNULL).communicate()
        return out.decode("utf-8").strip()

    def checkout(self):
        """
        Clone and checkout appropriate version from remote git repository.
        """
        self.print("  installing from remote [{}]".format(self.repository))
        (url, marker) = self.parse_repository()
        if not os.path.exists(self.clone):
            self.popen("git", "clone", url, self.clone)
        self.popen("git", "-C", self.clone, "reset", "--hard", "HEAD")
        self.popen("git", "-C", self.clone, "checkout", marker)
        self.popen("git", "-C", self.clone, "reset", "--hard", "HEAD")
        self.popen("git", "-C", self.clone, "pull")

    def parse_repository(self):
        url_match = re.match("(.+?)(@[^\/]+)?$", self.repository)
        (url, requested_version) = url_match.groups()
        if requested_version:
            requested_version = requested_version[1:]
            requested_version = re.sub("\#.*", "", requested_version)
        else:
            requested_version = "master"
        return url, requested_version

    def install_project(self):
        self.print("  install from local folder [{}]".format(self.clone))
        os.chdir(self.clone)
        sys.path.insert(0, self.clone)

        def x(*_, **kwargs):
            self.install_requires = kwargs.get("install_requires", [])

        setuptools.setup = x
        importlib.import_module("setup")
        self.popen(self.pip, "install", "--upgrade", ".")

    def install_venv(self):
        """
        Installs the Python virtual environment.
        """
        self.print(
            "  installing Python virtual environment in [{}]".format(
                self.venv))
        self.popen("/usr/bin/python3", "-m", "venv", self.venv)

    def upgrade_pip(self):
        """
        Upgrade pip to minimum required version.
        """
        self.popen(self.pip, "install", "--upgrade",
                   "pip>={:s}".format(".".join([str(i) for i in PIP_VERSION])))

    def uninstall(self):
        if os.path.exists(self.root):
            self.print("remove [{}]".format(self.root))
            shutil.rmtree(self.root)
        else:
            self.print("project root [{}] not found".format(self.root))

    def popen(self, *args):
        proc = Popen(args, env=self.env, stdout=PIPE, stderr=STDOUT)
        logfile = open(LOGFILE, "a", encoding="utf-8")
        stdout = []
        for line in proc.stdout:
            out = line.decode("utf-8")
            logfile.write(out)
            if (out.strip()
                    and (not out.startswith(" ")
                         or out.strip().startswith("core4.setup: "))):
                stdout.append(out)
                print("  " + out.strip())
        ret = proc.wait()
        logfile.close()
        assert ret == 0
        return "\n".join(stdout)

    def upgrade(self, test=False, force=False, be=False):
        self.check_for_upgrade()
        self.print("upgrading [{}]".format(self.project))
        data = self.read_config()
        self.repository = data["repository"]
        self.web = data["web"]
        current = data["commit"]
        if os.path.isdir(self.repository):
            self.clone = self.repository
            self.print("  installing from [{}]".format(self.clone))
        else:
            self.checkout()
        latest = self.get_local_commit()
        if self.web and not be:
            self.print("  will build web apps")
        if latest == current:
            self.print("  latest [{}] == current commit".format(latest))
            self.print("  no changes with [{}]".format(self.project))
        else:
            self.print("  latest [{}] != current commit [{}]".format(
                latest, current))
            self.print("  project [{}] requires upgrade".format(self.project))
        if force:
            self.print("  force upgrade with [{}]".format(self.project))
        if self.reset:
            self.print("  reset [{}]".format(self.project))
        if not test and (self.reset or force or latest != current):
            if self.reset:
                self.install([])
            else:
                self.install_project()
                self.write_config()
                if not be and self.web:
                    self.build([])

    def build(self, filter):
        self.print("  build webapps in [{}]".format(self.clone))
        for build in self.identify_webapp(self.clone):
            if (filter == [] or build["name"] in filter):
                self.print("    build [{}]".format(build["base"]))
                self.clean_webapp(os.path.join(build["base"], build["dist"]))
                self.build_webapp(build["base"], build["command"])
                self.install_webapp(build["base"], build["dist"])

    def install_webapp(self, base, dist):
        command = "import {p:s}; print({p:s}.__file__)".format(p=self.project)
        os.chdir(self.root)
        proc = Popen([self.python, "-c", command], env=self.env, stdout=PIPE,
                     stderr=STDOUT)
        (out, _) = proc.communicate()
        pkg_clone = os.path.join(self.clone, self.project)
        part = base[len(pkg_clone) + 1:]
        target = os.path.join(os.path.dirname(out.decode("utf-8")), part, dist)
        if os.path.exists(target):
            self.print("    clean [{}]".format(target))
            shutil.rmtree(target)
        source = os.path.join(base, dist)
        self.print("    copy [{}] to [{}]".format(source, target))
        shutil.copytree(source, target)

    def dependency_upgrade(self, package):
        self.print("upgrading package [{}] in [{}]".format(
            package, self.project))
        data = self.read_config()
        found = False
        install_requires = data.get("install_requires", [])
        for install in install_requires:
            name = re.split(r"[\@\<\>\=]+", install)[0]
            if name == package:
                self.print("  package found")
                self.popen(self.pip, "uninstall", "--yes", install)
                self.popen(self.pip, "install", install)
                found = True
        if not found:
            self.print("  not in scope of {}".format(install_requires))

    def version(self):
        args = [self.python, "-c", VERSION_COMMAND.format(p=self.project)]
        proc = Popen(args, env=self.env, stdout=PIPE, stderr=STDOUT)
        (stdout, stderr) = proc.communicate()
        data = self.read_config()
        self.repository = data["repository"]
        self.web = data["web"]
        core4_repository = [r for r in data["install_requires"]
                            if "/core4.git" in r]
        core4_repository = core4_repository[0] if core4_repository else ""
        current = data["commit"]
        if os.path.isdir(self.repository):
            self.clone = self.repository
        timestamp = self.get_commit_datetime(current)
        (version, build, core4_version, *core4_build) = stdout.decode(
            "utf-8").strip().split(", ")
        return {
            "repository": self.repository,
            "web": self.web,
            "version": version,
            "build": build,
            "commit": {
                "hash": data["commit"],
                "timestamp": timestamp
            },
            "core4": {
                "version": core4_version,
                "build": ", ".join(core4_build),
                "repository": core4_repository
            },
            "error": stderr or None
        }


class CoreUpdater(CoreBase, InstallMixin):

    def list_project(self, home=None):
        home = home or self.config.folder.home
        for project in os.listdir(home):
            yield project


def run(args):
    t0 = datetime.datetime.now()
    if args["PROJECT"]:
        project = args["PROJECT"]
    else:
        installer = CoreUpdater()
        project = installer.list_project(args["--home"])
    if args["install"]:
        installer = CoreInstaller(
            project[0], args["REPOSITORY"], args["--reset"],
            args["--web"], args["--home"])
        installer.install(args["--build"])
    elif args["upgrade"]:
        for p in project:
            installer = CoreInstaller(
                p, reset=args["--reset"], home=args["--home"])
            installer.upgrade(test=args["--test"], force=args["--force"],
                              be=args["--nobuild"])
    elif args["dep-upgrade"]:
        for p in project:
            if p != "core4":
                installer = CoreInstaller(p, home=args["--home"])
                installer.dependency_upgrade(args["PACKAGE"])
    elif args["uninstall"]:
        for p in project:
            installer = CoreInstaller(p, home=args["--home"])
            installer.uninstall()
    elif args["version"]:
        for p in project:
            installer = CoreInstaller(p, home=args["--home"])
            data = installer.version()
            print(p)
            if data["error"]:
                print("  ERROR:\n{}".format(data["error"]))
            else:
                print("  version: {} ({}) {} webapps".format(
                    data["version"], data["build"],
                    "with" if data["web"] else "without"))
                print("  commit:  {} ({})".format(
                    data["commit"]["timestamp"], data["commit"]["hash"]))
                print("  source:  {}".format(data["repository"]))
                print("  core4:   {}, build {} from {}".format(
                    data["core4"]["version"], data["core4"]["build"],
                    data["core4"]["repository"]))
    elif args["build"]:
        installer = WebBuilder()
        installer.init_vars(".")
        installer.build(args["--build"])
    else:
        raise SystemExit("nothing to do.")
    runtime = datetime.datetime.now() - t0
    print("done in %s.\n" % (runtime))


def main():
    args = docopt(__doc__, help=True)
    # print(args)
    run(args)


if __name__ == '__main__':
    main()
