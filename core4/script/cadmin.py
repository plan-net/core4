#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
cadmin - core-4 deployment utililty.

Usage:
  cadmin install [--reset] REPOSITORY PROJECT
  cadmin upgrade [--test] [--reset] [--force] [PROJECT]
  cadmin uninstall PROJECT

Arguments:
  REPOSITORY  requirements specifier with VCS support (see pip documentation)
  PROJECT     project name

Options:
  -r --reset                   reset existing project root
  -t --test                    dry-run
  -h --help                    show this screen
  -v --version                 show version
"""

import sys

# ensure python3
if sys.version_info < (3, 5):
    sys.exit('requires Python 3.5 or higher')

# ensure pip >= 18.1
import pip

PIP_VERSION = (18, 1)
if tuple([int(i) for i in pip.__version__.split(".")]) < PIP_VERSION:
    sys.exit("requires pip version 18.1 or higher, "
             "Upgrade with `pip install --upgrade pip`")

import os
from os.path import join, exists
from docopt import docopt
from core4.base.main import CoreBase
import core4.const
from subprocess import Popen, DEVNULL
import pkg_resources
import sh
import shutil
import re

INSTALL_PROJECT = "project.txt"
INSTALL_REQUIRES = "install_requires.txt"


class CoreAdminInstaller(CoreBase):

    def __init__(self, project, repository=None):
        super().__init__()
        self.project = project
        self.home = self.config.folder.home
        self.project_root = join(self.home, project)
        self.venv_root = join(self.project_root, core4.const.VENV)
        self.venv_pip = join(self.project_root, core4.const.VENV_PIP)
        self.repository = repository
        self.project_requirement = join(self.venv_root, INSTALL_PROJECT)
        self.env = os.environ
        if "PYTHONPATH" in self.env:
            print("remove PYTHONPATH={}".format(self.env["PYTHONPATH"]))
            del self.env["PYTHONPATH"]

    def reset(self):
        if exists(self.project_root):
            print("removing [{}]".format(self.project_root))
            shutil.rmtree(self.project_root)

    def check_for_install(self):
        if self.home is None or not exists(self.home):
            raise SystemExit("core4 config [folder.home] not set or None")
        if exists(self.project_root):
            raise SystemExit("project root [{}] exists".format(
                self.project_root))
        if exists(self.venv_root):
            raise SystemExit("virtual environment [{}] exists".format(
                self.venv_root))

    def install(self):
        curdir = os.curdir
        repository = self.project + " @ " + "git+" + self.repository
        requirement = next(pkg_resources.parse_requirements(repository))
        print("creating project root [{}]".format(self.project_root))
        os.makedirs(self.project_root)
        os.chdir(self.project_root)
        print("installing Python virtual environment in [{}]".format(
            self.venv_root))
        ret = Popen(["python3", "-m", "venv", self.venv_root], env=self.env,
                    stdout=DEVNULL).wait()
        assert ret == 0
        os.chdir(self.project_root)
        print("upgrading [pip]")
        ret = Popen(
            [join(self.venv_root, "bin/pip3"), "install", "--upgrade",
             "pip>={:s}".format(".".join([str(i) for i in PIP_VERSION]))
             ], stdout=DEVNULL, env=self.env).wait()
        assert ret == 0
        self.pip_install(requirement.url)
        os.chdir(curdir)
        print("\ndone.\n")

    def pip_install(self, url):
        print("installing [{}]".format(self.project))
        ret = Popen([self.venv_pip, "install", "--upgrade", url],
                    env=self.env).wait()
        assert ret == 0
        (url, marker) = self.parse_repository(url)
        commit_hash = self.get_commit(url, marker)
        print("commit hash [{}] at [{}] with [{}]".format(
            commit_hash, url, marker))
        with open(self.project_requirement, "w", encoding="utf-8") as fh:
            fh.write(commit_hash + " " + url[4:] + "@" + marker)

    def get_commit(self, url, marker):
        stdout = sh.git(["ls-remote", url[4:], marker])
        return stdout.split()[0].strip()

    def check_for_upgrade(self):
        if self.home is None or not exists(self.home):
            raise SystemExit("core4 config [folder.home] not set or None")
        if not exists(self.project_root):
            raise SystemExit("project root [{}] not found".format(
                self.project_root))
        if not exists(self.venv_root):
            raise SystemExit("virtual environment [{}] not found".format(
                self.venv_root))

    def parse_repository(self, repository):
        url_match = re.match("(.+?)(@[^\/]+)?$", repository)
        (url, requested_version) = url_match.groups()
        if requested_version:
            requested_version = requested_version[1:]
            requested_version = re.sub("\#.*", "", requested_version)
        else:
            requested_version = "master"
        return (url, requested_version)

    def upgrade(self, test=False, reset=False, force=False):
        with open(self.project_requirement, "r", encoding="utf-8") as fh:
            body = fh.read().strip()
        (local_commit, repos) = body.split()
        (url, marker) = self.parse_repository("git+" + repos)
        pass_url = re.sub("\://(.+)\:(.+)@", "://:\g<1>:****@", url)
        print("repository at [{}] with [{}]".format(pass_url, marker))
        remote_commit = self.get_commit(url, marker)
        print("  local commit [{}] {}".format(
            local_commit, "changed to [{}]".format(remote_commit)
            if local_commit != remote_commit else "no changes"))
        if force or local_commit != remote_commit:
            if not test:
                if force or reset:
                    self.repository = repos
                    self.reset()
                    self.install()
                else:
                    self.pip_install("git+" + repos)
            return True
        return False


class CoreAutoUpgrade(CoreBase):

    def upgrade(self, test=False, reset=False, force=False):
        print("folder.home = {}".format(self.config.folder.home))
        upgrades = []
        for project in os.listdir(self.config.folder.home):
            print("upgrading [{}]".format(project))
            admin = CoreAdminInstaller(project)
            if admin.upgrade(test, reset, force):
                upgrades.append(project)
        if upgrades:
            print("\nupgrades: {}".format(" ".join(upgrades)))
        else:
            print("\nno upgrades required")

def run(args):
    if args["install"]:
        installer = CoreAdminInstaller(args["PROJECT"], args["REPOSITORY"])
        if args["--reset"]:
            installer.reset()
        installer.check_for_install()
        installer.install()
    elif args["upgrade"]:
        if args["PROJECT"]:
            installer = CoreAdminInstaller(args["PROJECT"])
            installer.check_for_upgrade()
            installer.upgrade(args["--test"], args["--reset"], args["--force"])
        else:
            installer = CoreAutoUpgrade()
            installer.upgrade(args["--test"], args["--reset"], args["--force"])
    elif args["uninstall"]:
        installer = CoreAdminInstaller(args["PROJECT"])
        installer.reset()
    else:
        raise SystemExit("nothing to do.")


def main():
    run(args=docopt(__doc__, help=True))


if __name__ == '__main__':
    main()
