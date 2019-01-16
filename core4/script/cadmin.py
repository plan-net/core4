"""
cadmin - core4 deployment utililty.

Usage:
  cadmin --install [-r REPOS] [-c CORE4_REPOS] [--reset] PROJECT
  cadmin --upgrade [PROJECT] [--test]

Arguments:
  PROJECT  project name
Options:
  -r REPOS --repository=REPOS  project git repository
  -c REPOS --core4=REPOS       core4 git repository
  -x --reset                   reset existing project root
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
import venv
import subprocess
import sh
import shutil

PROJECT_REQUIRES = "project_requires.txt"
CORE4_REQUIRES = "core4_requires.txt"


class CoreAdminInstaller(CoreBase):

    def __init__(self, project, repository=None, core4_repository=None):
        super().__init__()
        self.project = project
        self.home = self.config.folder.home
        self.project_root = join(self.home, project)
        self.venv_root = join(self.project_root, core4.const.VENV)
        self.venv_pip = join(self.project_root, core4.const.VENV_PIP)
        if project == core4.const.CORE4:
            self.repository = repository or self.config.core4_origin
        else:
            self.repository = repository
        self.project_requirement = join(self.venv_root, PROJECT_REQUIRES)
        self.core4_requirement = join(self.venv_root, CORE4_REQUIRES)
        self.core4_repository = core4_repository or self.config.core4_origin

    def check_for_install(self):
        if self.home is None or not exists(self.home):
            raise SystemExit("core4 config [folder.home] not set or None")
        if exists(self.project_root):
            raise SystemExit("project root [{}] exists".format(
                self.project_root))
        if exists(self.venv_root):
            raise SystemExit("virtual environment [{}] exists".format(
                self.venv_root))

    def reset(self):
        if exists(self.project_root):
            print("removing [{}]".format(self.project_root))
            shutil.rmtree(self.project_root)

    def check_for_upgrade(self):
        if self.home is None or not exists(self.home):
            raise SystemExit("core4 config [folder.home] not set or None")
        if not exists(self.project_root):
            raise SystemExit("project root [{}] not found".format(
                self.project_root))
        if not exists(self.venv_root):
            raise SystemExit("virtual environment [{}] not found".format(
                self.venv_root))

    def install(self):
        print("creating project root [{}]".format(self.project_root))
        os.makedirs(self.project_root)
        os.chdir(self.project_root)
        print("installing Python virtual environment in [{}]".format(
            self.venv_root))
        builder = venv.EnvBuilder(system_site_packages=False, clear=False,
                                  symlinks=False, upgrade=False, with_pip=True)
        builder.create(self.venv_root)
        print("upgrading pip")
        subprocess.Popen(
            [join(self.venv_root, "bin/pip3"), "install", "--upgrade",
             "pip>={:s}".format(".".join([str(i) for i in PIP_VERSION]))
             ]).communicate()
        if self.project != core4.const.CORE4:
            print("write [{}]".format(self.core4_requirement))
            with open(self.core4_requirement, "w", encoding="utf-8") as fh:
                fh.write("git+" + self.core4_repository + "\n")
            print("install core4")
            subprocess.Popen(
                [self.venv_pip, "install", "--upgrade", "--requirement",
                 self.core4_requirement]).communicate()
        print("write [{}]".format(self.project_requirement))
        with open(self.project_requirement, "w", encoding="utf-8") as fh:
            fh.write("git+" + self.repository + "\n")
        print("install project")
        subprocess.Popen(
            [self.venv_pip, "install", "--upgrade", "--requirement",
             self.project_requirement]).communicate()
        print("done.")

    def upgrade(self, test=False):
        print("upgrading [{}]".format(self.project))
        upgrades = []
        for pkg, requirement in (
                (core4.const.CORE4, self.core4_requirement),
                (self.project, self.project_requirement)):
            if exists(requirement):
                print("  work [{}]".format(pkg))
                with open(requirement, "r", encoding="utf-8") as fh:
                    repository = fh.read().strip()
                print("    connect [{}]".format(repository))
                current = self.get_current_version(pkg)
                print("      current [{}]".format(current), end="")
                if '@' in repository:
                    (repository, *frozen) = repository.split("@")
                    print(" == fixed [{}]".format(frozen[0]), end="")
                    frozen = frozen[0]
                else:
                    frozen = None
                latest = self.get_latest_version(repository)
                if frozen is None:
                    if latest == current:
                        print(" == ", end="")
                    elif latest is not None:
                        print(" != ", end="")
                    else:
                        print(" !! ", end="")
                    print("latest [{}]".format(latest), end="")
                    if latest is not None and latest != current:
                        print(" <=== UPDATE REQUIRED", end="")
                        upgrades.append((pkg, repository))
                print()
        if not test:
            for pkg, repository in upgrades:
                self._run_upgrade(pkg, repository)

    def _run_upgrade(self, package, repository):
        print("  upgrading [{}] from [{}]".format(package, repository))
        subprocess.Popen([self.venv_pip, "install", "--upgrade",
                          repository]).communicate()

    def get_latest_version(self, repository):
        if repository.startswith("git+"):
            repository = repository[4:]
        stdout = sh.git(["ls-remote", "--tags", repository])
        vlist = []
        for line in stdout.split("\n"):
            if line:
                (commit, *tag) = line.split()
                version = " ".join(tag).split("/")[-1]
                vlist.append(version)
        if vlist:
            vlist = sorted([[int(u) for u in i.split(".")] for i in vlist])
            latest = vlist[-1]
            return ".".join([str(i) for i in latest])
        return None

    def get_current_version(self, package):
        proc = subprocess.Popen([self.venv_pip, "freeze"],
                                stdout=subprocess.PIPE)
        (stdout, _) = proc.communicate()
        for line in stdout.decode("utf-8").split("\n"):
            if line.startswith(package + "=="):
                return line[len(package + "=="):].strip()
        return None


class CoreAutoUpgrade(CoreBase):

    def upgrade(self, test=False):
        print("folder.home = {}".format(self.config.folder.home))
        for project in os.listdir(self.config.folder.home):
            admin = CoreAdminInstaller(project)
            admin.upgrade(test)


def main():
    args = docopt(__doc__, help=True)
    if args["--install"]:
        installer = CoreAdminInstaller(
            args["PROJECT"], args["--repository"], args["--core4"])
        if args["--reset"]:
            installer.reset()
        installer.check_for_install()
        installer.install()
    elif args["--upgrade"]:
        if args["PROJECT"]:
            installer = CoreAdminInstaller(args["PROJECT"])
            installer.check_for_upgrade()
            installer.upgrade(args["--test"])
        else:
            installer = CoreAutoUpgrade()
            installer.upgrade(args["--test"])

    else:
        raise SystemExit("nothing to do.")


if __name__ == '__main__':
    main()
