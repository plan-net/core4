"""
cadmin - core4 administration utililty.

Usage:
  cadmin --install [-r REPOS] [-c CORE4_REPOS] PROJECT
  cadmin [--test] --upgrade [PROJECT]

Arguments:
  PROJECT  project name
Options:
  -r REPOS --repository=REPOS  project git repository
  -c REPOS --core4=REPOS       core4 git repository
  -t --test                    dry-run
  -h --help                    show this screen
  -v --version                 show version
"""

# todo: install specific version and upgrade against this version

import sys

# ensure this is python3
version = float("%d.%d" % (sys.version_info.major, sys.version_info.minor))
if version < 3.5:
    raise Exception("Must be using Python 3.5 or higher.\n"
                    "This is Python %s" % (version))

# ensure pip >= 18.1
import pip

version = float("%d.%d" % (
    tuple([int(i) for i in pip.__version__.split(".")[:2]])))
if version < 18.1:
    raise Exception("Must be using pip 18.1 or higher.\n"
                    "This is pip %s. "
                    "Upgrade with pip install --upgrade pip" % (version))

import os
from docopt import docopt
from core4.base.main import CoreBase
import venv
import core4.const
import subprocess
import sh


class CoreAdmin(CoreBase):

    def install(self, project, repository, core4_repository):
        core4_home = self.config.folder.home
        project_root = os.path.join(core4_home, project)
        venv_root = os.path.join(project_root, core4.const.VENV)
        upgrade_requires = os.path.join(venv_root, "upgrade_requires.txt")

        if core4_home is None or not os.path.exists(core4_home):
            raise SystemExit("core4 config [folder.home] not set or None")
        if os.path.exists(project_root):
            raise SystemExit("project root [{}] exists".format(project_root))
        if os.path.exists(venv_root):
            raise SystemExit("virtual environment [{}] exists".format(
                venv_root))

        print("creating project root [{}]".format(project_root))
        os.makedirs(project_root)
        os.chdir(project_root)

        print("installing Python virtual environment in [{}]".format(
            venv_root))
        builder = venv.EnvBuilder(system_site_packages=False, clear=False,
                                  symlinks=False, upgrade=False, with_pip=True)
        builder.create(venv_root)

        with open(upgrade_requires, "w", encoding="utf-8") as fh:
            fh.write("git+" + repository + "\n")

        self._upgrade_requires(venv_root)
        print("done.")

    def _upgrade_requires(self, venv_root):
        venv_pip = os.path.join(venv_root, "bin/pip3")
        print("upgrading pip")
        upgrade_requires = os.path.join(venv_root, "upgrade_requires.txt")
        # upgrade pip
        proc = subprocess.Popen([venv_pip, "install", "--upgrade", "pip>=18.1"])
        proc.communicate()
        # install project package
        print("install package and dependencies")
        proc = subprocess.Popen(
            [venv_pip, "install", "--upgrade", "--requirement",
             upgrade_requires])
        proc.communicate()

    def upgrade(self, project, test=False):
        remote = list(self._remote(project))
        print("upgrade [{}]".format(project))
        test = []
        if project != core4.const.CORE4:
            test.append((core4.const.CORE4, remote.pop(0)))
        test.append((project, remote.pop(0)))
        for mod in test:
            version = self._installed_version(project, mod[0])
            latest = self._remote_latest(mod[1])
            print("  found [{}] version [{}], ".format(
                mod[0], version, latest), end="")
            if version != latest:
                print("latest [{}] <= requires update".format(latest))
            else:
                print("up-to-date")
        if not test:
            print("run")

        # if self.requires_upgrade(project):
        #     print("upgrading [{}]".format(project))
        #     core4_home = self.config.folder.home
        #     project_root = os.path.join(core4_home, project)
        #     venv_root = os.path.join(project_root, core4.const.VENV)
        #     self._upgrade_requires(venv_root)

    def upgrade_all(self, test=False):
        core4_home = self.config.folder.home
        for project in os.listdir(core4_home):
            self.upgrade(project, test)

    def _remote(self, project):
        core4_home = self.config.folder.home
        project_root = os.path.join(core4_home, project)
        venv_root = os.path.join(project_root, core4.const.VENV)
        upgrade_requires = os.path.join(venv_root, "upgrade_requires.txt")
        fh = open(upgrade_requires, "r", encoding="utf-8")
        repos = fh.readlines()
        fh.close()
        for line in repos:
            line = line.strip()
            if line.startswith("git+"):
                line = line[4:]
            yield line

    def _remote_latest(self, repository):
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

    def _installed_version(self, project, module):
        core4_home = self.config.folder.home
        project_root = os.path.join(core4_home, project)
        venv_root = os.path.join(project_root, core4.const.VENV)
        venv_python = os.path.join(venv_root, "bin/python")
        proc = subprocess.Popen(
            [venv_python, "-c",
             "import {mod}; print({mod}.__version__)".format(mod=module)],
            stdout=subprocess.PIPE)
        (stdout, _) = proc.communicate()
        version = stdout.decode("utf-8").strip()
        return version

    def requires_upgrade(self, project):
        version = self._installed_version(project)
        print("found [{}] in version [{}]".format(project, version), end="")
        if project != core4.const.CORE4:
            core4_version = self._installed_version(core4.const.CORE4)
            print(", [{}] in version [{}]".format(core4.const.CORE4,
                                                  core4_version))
        else:
            print()


def main():
    admin = CoreAdmin()
    args = docopt(__doc__, help=True)
    if args["--install"]:
        admin.install(
            project=args["PROJECT"],
            repository=args["--repository"],
            core4_repository=args["--core4"]
        )
    elif args["--upgrade"]:
        if args["PROJECT"]:
            admin.upgrade(args["PROJECT"], args["--test"])
        else:
            admin.upgrade_all(args["--test"])
    else:
        raise SystemExit("nothing to do.")


if __name__ == '__main__':
    main()

"""
develop core4
    upgrade core4 and packages

    cadmin --develop core4

    export CORE4_DEV=/tmp/core4.dev
    export CORE4_REPOSITORY=ssh://git.bi.plan-net.com/srv/git/core4.git
    export CORE4_PROJECT=core4

    cd $CORE4_DEV  # might be the project home of your IDE, e.g. ~/PycharmProjects
    git clone $CORE4_REPOSITORY
    cd core4
    python3 -m venv .venv
    . .venv/bin/activate

    pip install -e .[tests]

    # here: install local.yaml
    mkdir ~/.core4
    nano ~/.core4/local.yaml

        DEFAULT:
          mongo_url: mongodb://core:654321@localhost:27017
          mongo_database: core4dev

        folder:
          home: /tmp/core4.dev

        logging:
          mongodb: INFO

        worker:
          min_free_ram: 16

        api:
          setting:
            cookie_secret: hello world
          token:
            secret: hello world again

        core4_origin: git+ssh://git.bi.plan-net.com/srv/git/core4.git

    # upgrade with git flow on master, develop and feature branches

develop project and core4 together
    upgrade packages

    cadmin --develop mypro

    export CORE4_DEV=/tmp/core4.dev
    export CORE4_REPOSITORY=ssh://git.bi.plan-net.com/srv/git/core4.git
    export CORE4_PROJECT=mypro
    export CORE4_PROJECT_REPOSITORY=file:///home/mra/core4.dev/mypro/.repos

    cd $CORE4_DEV  # might be the project home of your IDE, e.g. ~/PycharmProjects
    git clone $CORE4_PROJECT_REPOSITORY $CORE4_PROJECT
    cd $CORE4_PROJECT

    python3 -m venv .venv
    . enter_env

    export PYTHONPATH=/tmp/core4.dev/core4:/tmp/core4.dev/core4/.venv/lib/python3.5/site-packages


cadmin --upgrade --all


"""
