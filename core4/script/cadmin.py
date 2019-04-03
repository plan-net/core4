#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
cadmin - core-4 deployment utililty.

Usage:
  cadmin install [--reset] [--web] REPOSITORY PROJECT
  cadmin upgrade [--test] [--reset] [--web] [--force] [PROJECT]
  cadmin uninstall PROJECT

Arguments:
  REPOSITORY  requirements specifier with VCS support (see pip documentation)
  PROJECT     project name

Options:
  -r --reset    reset existing project root
  -t --test     dry-run
  -w --web      build and install web apps
  -h --help     show this screen
  -v --version  show version
"""

import sys

# ensure python3
if sys.version_info < (3, 5):
    sys.exit('requires Python 3.5 or higher')

# ensure pip >= 18.1
import pip

#: minimum required pip version
PIP_VERSION = (18, 1)
if tuple([int(i) for i in pip.__version__.split(".")]) < PIP_VERSION:
    sys.exit("requires pip version 18.1 or higher, "
             "Upgrade with `pip install --upgrade pip`")

import os
from os.path import join, exists
from docopt import docopt
from core4.base.main import CoreBase
import core4.const
from subprocess import Popen, DEVNULL, PIPE, STDOUT
import datetime
import sh
import shutil
import re

#: file to save the project latest commit and repository source
INSTALL_PROJECT = "project.txt"

LOGFILE = os.path.join(os.path.abspath("."), "cadmin.log")
if os.path.exists(LOGFILE):
    os.unlink(LOGFILE)


class InstallMixin():
    def print(self, msg):
        logfile = open(LOGFILE, "a", encoding="utf-8")
        logfile.write(msg + "\n")
        logfile.close()
        print(msg)


class CoreAdminInstaller(CoreBase, InstallMixin):

    def __init__(self, project, repository=None, web=False):
        super().__init__()
        self.project = project
        self.home = self.config.folder.home
        self.project_root = join(self.home, project)
        self.remote = join(self.project_root, "remote")
        self.venv_root = join(self.project_root, core4.const.VENV)
        self.venv_pip = join(self.project_root, core4.const.VENV_PIP)
        self.venv_python = join(self.project_root, core4.const.VENV_PYTHON)
        self.repository = repository
        self.project_requirement = join(self.venv_root, INSTALL_PROJECT)
        self.env = os.environ
        self.env["PYTHONPATH"] = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "installer")
        self.web = web

    def reset(self):
        if exists(self.project_root):
            self.print("removing [{}]".format(self.project_root))
            shutil.rmtree(self.project_root)

    def check_for_install(self):
        """
        Verify ``folder.home`` is defined, project does not exist,
        and no virtual environment exists, yet.
        """
        if self.home is None or not exists(self.home):
            raise SystemExit("core4 config [folder.home] not set or None")
        if exists(self.project_root):
            raise SystemExit("project root [{}] exists".format(
                self.project_root))
        if exists(self.venv_root):
            raise SystemExit("virtual environment [{}] exists".format(
                self.venv_root))

    def install(self):
        """
        Create project folder, install environment, upgrade pip and install
        from local or remote repository.
        """
        self.print("installing [{}]".format(self.project))
        os.makedirs(self.project_root)
        self.print("  created project root [{}]".format(self.project_root))
        self.install_environment()
        self.upgrade_pip()
        if os.path.exists(self.repository):
            commit_hash = self.pip_install_local(self.repository)
        else:
            commit_hash = self.pip_install_remote(self.repository)
            self.pip_install_local(self.remote)
        self.write_commit(commit_hash)

    def write_commit(self, commit_hash):
        """
        Writes the commit hash and repository location into
        ``.venv/project.txt``.
        """
        with open(self.project_requirement, "w", encoding="utf-8") as fh:
            fh.write(commit_hash + " " + self.repository)

    def upgrade_pip(self):
        """
        Upgrade pip to minimum required version.
        """
        self.print("  upgrading [pip]")
        ret = Popen(
            [join(self.venv_root, "bin/pip3"), "install", "--upgrade",
             "pip>={:s}".format(".".join([str(i) for i in PIP_VERSION]))
             ], stdout=DEVNULL, env=self.env).wait()
        assert ret == 0

    def install_environment(self):
        """
        Installs the Python virtual environment.
        """
        self.print("  installing Python virtual environment in [{}]".format(
            self.venv_root))
        ret = Popen(["python3", "-m", "venv", self.venv_root], env=self.env,
                    stdout=DEVNULL).wait()
        assert ret == 0

    def pip_install_remote(self, repository):
        """
        Clone and checkout appropriate version from remote git repository.
        """
        self.print("  installing from remote [{}]".format(repository))
        (url, marker) = self.parse_repository(repository)
        sh.git(["clone", url, self.remote])
        sh.git(["-C", self.remote, "checkout", marker])
        commit_hash = self.get_remote_commit(url, marker)
        self.print("  commit [{}] at [{}] with [{}]".format(
            commit_hash, url, marker))
        return commit_hash

    def pip_upgrade_remote(self, repository):
        """
        Upgrade the local worktree in ``./remote``.
        """
        self.print("  upgrading from remote [{}]".format(repository))
        (url, marker) = self.parse_repository(repository)
        sh.git(["-C", self.remote, "reset", "--hard", "HEAD"])
        sh.git(["-C", self.remote, "checkout", marker])
        sh.git(["-C", self.remote, "fetch", "--all"])
        sh.git(["-C", self.remote, "pull"])
        commit_hash = self.get_remote_commit(url, marker)
        self.print("  commit [{}] at [{}] with [{}]".format(
            commit_hash, url, marker))
        return commit_hash

    def pip_install_local(self, source):
        """
        Build the webapps distributions if requested and upgrade the Python
        package.
        """
        self.print("  upgrading from local folder [{}]".format(source))
        os.chdir(source)
        if self.web:
            self.popen(self.venv_python, "setup.py", "build_web")
        os.chdir(source)
        self.popen(self.venv_pip, "-v", "install", "--upgrade", ".")
        commit_hash = self.get_local_commit()
        self.print("  commit [{}] at [{}]".format(
            commit_hash, source))
        return commit_hash

    def get_remote_commit(self, url, marker):
        """
        Retrieve latest commit from a remote repository.
        """
        stdout = sh.git(["ls-remote", url, marker])
        return stdout.split()[0].strip()

    def get_local_commit(self):
        """
        Retrieve the latest commit from a local worktree.
        """
        stdout = sh.git(["--no-pager", "log", "-1", "--pretty=%H"])
        return stdout.strip()

    def check_for_upgrade(self):
        """
        Verify ``folder.home`` is defined, project does exists,
        and virtual environment exists.
        """
        if self.home is None or not exists(self.home):
            raise SystemExit("core4 config [folder.home] not set or None")
        if not exists(self.project_root):
            raise SystemExit("project root [{}] not found".format(
                self.project_root))
        if not exists(self.venv_root):
            raise SystemExit("virtual environment [{}] not found".format(
                self.venv_root))

    def upgrade(self, test=False, reset=False, force=False):
        self.print("upgrading [{}]".format(self.project))
        with open(self.project_requirement, "r", encoding="utf-8") as fh:
            body = fh.read().strip()
        (local_commit, repos) = body.split()
        if os.path.exists(repos):
            os.chdir(repos)
            self.print("  repository at [{}]".format(repos))
            remote_commit = self.get_local_commit()
        else:
            (url, marker) = self.parse_repository(repos)
            pass_url = re.sub("\://(.+)\:(.+)@", "://:\g<1>:****@", url)
            self.print("  repository at [{}] with [{}]".format(
                pass_url, marker))
            remote_commit = self.get_remote_commit(url, marker)
        self.print("  local commit [{}] {}".format(
            local_commit, "changed to [{}]".format(remote_commit)
            if local_commit != remote_commit else "no changes"))
        if force or local_commit != remote_commit:
            webapps_file = os.path.join(
                os.path.dirname(self.venv_python), "..", "webapps.dist")
            if os.path.exists(webapps_file):
                self.web = True
                self.print("  found existing [{}] to build webapps".format(
                           webapps_file))
            if not test:
                if reset:
                    self.repository = repos
                    self.reset()
                    self.install()
                else:
                    if os.path.exists(repos):
                        commit_hash = self.pip_install_local(repos)
                    else:
                        commit_hash = self.pip_upgrade_remote(repos)
                        self.pip_install_local(self.remote)
                    with open(self.project_requirement, "w",
                              encoding="utf-8") as fh:
                        fh.write(commit_hash + " " + repos)
            return True
        return False

    def parse_repository(self, repository):
        url_match = re.match("(.+?)(@[^\/]+)?$", repository)
        (url, requested_version) = url_match.groups()
        if requested_version:
            requested_version = requested_version[1:]
            requested_version = re.sub("\#.*", "", requested_version)
        else:
            requested_version = "master"
        return (url, requested_version)

    def popen(self, *args):
        proc = Popen(args, env=self.env, stdout=PIPE, stderr=STDOUT)
        logfile = open(LOGFILE, "a", encoding="utf-8")
        for line in proc.stdout:
            out = line.decode("utf-8")
            logfile.write(out)
            if (out.strip()
                    and (not out.startswith(" ")
                         or out.strip().startswith("core4.setup: "))):
                print("  " + out.strip())
        ret = proc.wait()
        logfile.close()
        assert ret == 0


class CoreAutoUpgrade(CoreBase, InstallMixin):

    def upgrade(self, test=False, reset=False, force=False, web=False):
        self.print("folder.home = {}".format(self.config.folder.home))
        upgrades = []
        for project in os.listdir(self.config.folder.home):
            admin = CoreAdminInstaller(project, web=web)
            if admin.upgrade(test, reset, force):
                upgrades.append(project)
        if upgrades:
            self.print("upgrades: {}".format(" ".join(upgrades)))
        else:
            self.print("no upgrades required")


def run(args):
    t0 = datetime.datetime.now()
    if args["install"]:
        installer = CoreAdminInstaller(args["PROJECT"], args["REPOSITORY"],
                                       args["--web"])
        if args["--reset"]:
            installer.reset()
        installer.check_for_install()
        installer.install()
    elif args["upgrade"]:
        if args["PROJECT"]:
            installer = CoreAdminInstaller(args["PROJECT"], web=args["--web"])
            installer.check_for_upgrade()
            installer.upgrade(args["--test"], args["--reset"], args["--force"])
        else:
            installer = CoreAutoUpgrade()
            installer.upgrade(args["--test"], args["--reset"], args["--force"],
                              args["--web"])
    elif args["uninstall"]:
        installer = CoreAdminInstaller(args["PROJECT"])
        installer.reset()
    else:
        raise SystemExit("nothing to do.")
    runtime = datetime.datetime.now() - t0
    print("done in %s.\n" % (runtime))


def main():
    run(args=docopt(__doc__, help=True))


if __name__ == '__main__':
    main()
