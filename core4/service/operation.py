#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import re
import sys
import textwrap
import json
import sh
from warnings import warn
import core4.util.node
from core4.base.main import CoreBase
import datetime
from subprocess import Popen, STDOUT, PIPE
import pathlib
import shutil

NO_PROJECT = "WARNING!\nThis is not a core4 project."

PENDING_RELEASE = "WARNING!\nPending {release:s} found. You cannot " \
                  "--build if a pending release exist. Please commit new " \
                  "features into branch [develop]. Minor changes and bugfixes " \
                  "should go into {release:s}"

NO_PENDING_RELEASE = "WARNING!\nNo pending release found. You cannot " \
                     "--release with no pending --build. Checkout branch " \
                     "[develop] first and run `coco --build`."

NOT_DEVELOP = "WARNING!\nYour current branch is not [develop].\nYou have " \
              "to change branch from [{branch:s}] to [develop]."

NOT_MASTER = "WARNING!\nYour current branch is not [master].\nYou have to " \
             "change branch from [{branch:s}] to [master]."

NOT_CLEAN = "WARNING!\nYour working tree is not clean. Please commit or " \
            "stash your changes."

NO_BUILD_COMMITS = "WARNING!\nNo unreleased commits/changes found. Why " \
                   "build a new release?"

NO_RELEASE_COMMITS = "WARNING!\nNo unreleased commits/changes found. Why " \
                     "release {release:s}?"

NOT_MERGED = "WARNING!\nThe pending release has not been merged into " \
             "[{branch:s}]. You have to `git merge {release:s}`, first."

DIST_OUT_OF_DATE = "WARNING!\nWebapps have been found " \
                   "with ./dist folder not up-to-date. Run coco --dist, first."

MANIFEST = "MANIFEST.in"
RLIB = "../lib/R"
R_REQUIREMENTS = "r.txt"


class CoreBuilder(CoreBase):

    def __init__(self, project, *args, **kwargs):
        """
        Instantiate the builder with the project name.

        :param project: name (str)
        :param args:
        :param kwargs:
        """
        super().__init__()
        self._project = project
        self._step = False
        self._init_file = None
        self.major = None
        self.minor = None
        self.patch = None
        self._body = None
        self._version_line = None
        self._built_line = None

    def is_project(self):
        """
        Validates that the current path contains a core4 project. Indicator for
        core4 projects is the ``project == "core4"`` variable in the package
        ``__init__.py`` file. Additionally, this method extracts the version
        and the previous build timestamp.

        :return: bool indicating if this is a core4 project (``True``)
        """
        self._init_file = os.path.join(self._project, "__init__.py")
        if not os.path.exists(self._init_file):
            return False
        fh = open(self._init_file, "r", encoding="utf-8")
        in_scope = False
        lno = 0
        self._body = []
        for line in fh:
            if re.match(r"""^__project__\s*\=\s*["']core4["']\s*""", line):
                in_scope = True
            else:
                match = re.match(
                    r"""^__version__\s*\=\s*["']\s*(.+?)\s*["'].*""", line)
                if match is not None:
                    nums = re.split(r"\D", match.groups()[0])
                    (self.major, self.minor, self.patch) = [int(i) for i in
                                                            nums]
                    self._version_line = lno
                elif re.match(r"""^__built__\s*\=\s*.+?\s*""", line):
                    self._built_line = lno
            self._body.append(line.strip())
            lno += 1
        fh.close()
        return in_scope

    def pending_release(self):
        """
        Check if a current release exists. An existing git branch with naming
        convention ``release-#.#.#`` indicates a pending release.

        :return: boold indicating if a release exists and is pending.
        """
        for line in sh.git(["branch", "-a", "--no-color"]).split("\n"):
            match = re.match(r".+\s+(release-\d+\.\d+\.\d+)", line)
            if match:
                return match.groups()[0]
        return None

    def current_branch(self):
        """
        Queries the current git branch.

        :return: branch (str)
        """
        for line in sh.git(["branch", "--no-color"]).split("\n"):
            if line.strip().startswith("*"):
                return line[2:]
        raise RuntimeError("no branch found")

    def is_clean(self):
        """
        Verifies the current working tree is clean

        :return: ``True`` if clean, else ``False``
        """
        return sh.git(["status", "--porcelain"]) == ""

    def is_merged(self, release):
        """
        Verifies the passed branch has been merged into the current branch.

        :param release: branch to check
        :return: ``True`` if passed branch is merged, else ``False``
        """
        for line in sh.git(["branch", "-a", "--no-color", "--merged"]):
            if line.strip() == release.strip():
                return True
        return False

    def has_commits(self, left, right):
        """
        Compares to branches and counts the number of commits.

        :param left: left branch (str)
        :param right: right branch (str)
        :return: ``True`` if there are commits, else ``False``
        """
        out = sh.git(["rev-list", "--count", "%s..%s" % (left, right)])
        return int(out) > 0

    def create_release(self, major, minor, patch):
        """
        Creates a new branch with the naming convention
        ``release-[major].[minor].[patch]``.

        :param major: major release number
        :param minor: minor release number
        :param patch: patch release number
        """
        sh.git(["checkout", "-b", "release-%d.%d.%d" % (major, minor, patch)])

    def bump(self, major, minor, patch):
        """
        Creates a new commit with the next release number.

        :param major: major release number
        :param minor: minor release number
        :param patch: patch release number
        """
        sh.git(["commit", ".", "-m",
                "bump release-%d.%d.%d" % (major, minor, patch)])

    def git_push(self, major, minor, num):
        """
        Push all changes to remote using the naming convention
        ``release-[major].[minor].[patch]``.

        :param major: major release number
        :param minor: minor release number
        :param patch: patch release number
        """
        # git push --set-upstream origin release-0.0.3
        sh.git(["push", "--set-upstream", "origin",
                "release-%d.%d.%d" % (major, minor, num)])

    def git_push_tag(self):
        """
        Push all changes including the tags.
        """
        sh.git(["push"])
        sh.git(["push", "--tags"])

    def step(self, message):
        """
        Step indicator with passed message.

        :param message: str
        """
        print("[        ]  {}".format(message), end="\r")
        print("[        ]  ", end="")
        sys.stdout.flush()
        self._step = True

    def ok(self):
        """
        Feedback for a successful step.
        """
        print("\r[   OK   ]")
        self._step = False

    def exit(self, message, code=1):
        """
        Feedback for a failed step and exit.
        """
        if self._step:
            print("\r[ FAILED ]\n")
        print("\n".join(textwrap.wrap(message, 60)))
        print()
        sys.exit(code)

    def headline(self, message):
        """
        Feedback the passed message as a headline.

        :param message: str
        """
        print(message)
        print("=" * len(message))
        print()

    def get_number(self, message, default):
        """
        Input method to get an integer with the passed message and default
        value.

        :param message: str
        :param default: value
        :return: user input (int)
        """
        while True:
            print("  %-s [%d] > " % (message, default), end="")
            choice = input()
            if choice.strip() == "":
                choice = str(default)
            if choice.isnumeric():
                return int(choice)

    def mark_release(self, major, minor, patch):
        """
        Mark the source code with the release and build timestamp before
        :meth:`.bump`.

        :param major: major release number
        :param minor: minor release number
        :param patch: patch release number
        """
        lno = 0
        body = []
        for line in self._body:
            if lno == self._version_line:
                body.append('__version__ = "%d.%d.%d"' % (major, minor, patch))
            elif lno == self._built_line:
                body.append('__built__ = "%s"' % (core4.util.node.mongo_now()))
            else:
                body.append(line)
            lno += 1
        fh = open(self._init_file, "w", encoding="utf-8")
        for line in body:
            fh.write("%s\n" % (line))

    def checkout(self, branch):
        """
        Checkout the passed banch.

        :param branch: to checkout (str)
        """
        sh.git(["checkout", branch])

    def git_tag(self):
        """
        Create tag with the next release.
        """
        sh.git(["tag", "%d.%d.%d" % (self.major, self.minor, self.patch)])

    def remove_branch(self, branch):
        """
        Remove the passed release from local working tree and from the remote
        repository.

        :param branch: str
        """
        sh.git(["branch", "-d", branch])
        sh.git(["push", "origin", "--delete", branch])


def build(*args):
    """
    Interactive build of a new release. These are the following steps:

    #. verify current directory is a core4 project
    #. verify no pending release exists
    #. verify current branch is ``develop``
    #. verify the working tree is clean
    #. verify commits exist
    #. input the next release number in format ``[major].[minor].[patch]``
    #. create a branch with naming convention ``[major].[minor].[patch]``
    #. mark the source code with the release (version and build timestamp)
    #. bump a new commit with the release branch
    #. push all changes to remote repository

    :param args: three arguments with ``major``, ``minor`` and ``patch``
        release number to automatically create the next release
    """
    project = os.path.basename(os.path.abspath(os.curdir))
    b = CoreBuilder(project)

    print()
    b.headline("CORE4: project [{}] build process".format(project))

    b.step("verify core4 project")
    if not b.is_project():
        b.exit(NO_PROJECT, 1)
    b.ok()

    b.step("no pending release")
    pending_release = b.pending_release()
    if pending_release is not None:
        b.exit(PENDING_RELEASE.format(release=pending_release), 2)
    b.ok()

    b.step("this is branch [develop]")
    branch = b.current_branch()
    if branch != "develop":
        b.exit(NOT_DEVELOP.format(branch=branch), 3)
    b.ok()

    b.step("working tree is clean")
    if not b.is_clean():
        b.exit(NOT_CLEAN.format(), 4)
    b.ok()

    b.step("commits exist")
    if not b.has_commits("master", "develop"):
        b.exit(NO_BUILD_COMMITS.format(), 5)
    b.ok()

    b.step("webapps are up-to-date")
    if not dist(False, dryrun=True, quiet=True):
        b.exit(DIST_OUT_OF_DATE)
    b.ok()

    print()
    b.headline("define next release version")
    print("current local release: [%d.%d.%d]\n" % (b.major, b.minor, b.patch))
    # todo: could be that local latest is different to remote latest
    if args:
        (major, minor, num, *_) = args
    else:
        major = b.get_number("major", b.major)
        minor = b.get_number("minor", b.minor)
        num = b.get_number("build", b.patch + 1)

    print()
    if (major, minor, num) <= (b.major, b.minor, b.patch):
        b.exit("WARNING!\nCurrent release is higher/equal to next release "
               "[%d.%d.%d]. Please update the next release version.", 6)

    print("next release: [%d.%d.%d]\n" % (major, minor, num))

    b.step("create new release [%d.%d.%d]" % (major, minor, num))
    b.create_release(major, minor, num)
    b.ok()

    b.step("mark release [%d.%d.%d]" % (major, minor, num))
    b.mark_release(major, minor, num)
    b.ok()

    b.step("bump version")
    b.bump(major, minor, num)
    b.ok()

    b.step("push new release")
    b.git_push(major, minor, num)
    b.ok()

    print("\ndone.")


def release():
    """
    Finalize the current release. These are the following steps:

    #. verify current directory is a core4 project
    #. verify a pending release exists
    #. verify current branch is ``master``
    #. verify the working tree is clean
    #. verify the release has been merged into master
    #. verify the release has been merged into develop
    #. tag master branch with the release number
    #. push changes into branch master
    #. push changes into branch develop
    #. remove the release branch
    #. checkout into branch master
    """
    project = os.path.basename(os.path.abspath(os.curdir))
    b = CoreBuilder(project)

    print()
    b.headline("CORE4: project [{}] release process".format(project))

    b.step("verify core4 project")
    if not b.is_project():
        b.exit(NO_PROJECT, 1)
    b.ok()

    b.step("pending release")
    pending_release = b.pending_release()
    if pending_release is None:
        b.exit(NO_PENDING_RELEASE, 2)
    b.ok()

    b.step("this is branch [master]")
    branch = b.current_branch()
    if branch != "master":
        b.exit(NOT_MASTER.format(branch=branch), 3)
    b.ok()

    b.step("working tree is clean")
    if not b.is_clean():
        b.exit(NOT_CLEAN.format(), 4)
    b.ok()

    # b.step("commits exist")
    # if b.has_commits("master", pending_release):
    #     b.exit(NO_RELEASE_COMMITS.format(release=pending_release))
    # b.ok()

    (_, next_major, next_minor, next_build) = re.split(r"\D+", pending_release)

    b.step("release [{:s}.{:s}.{:s}] has been merged into [master]".format(
        next_major, next_minor, next_build
    ))
    if not b.is_merged(pending_release):
        b.exit(NOT_MERGED.format(release=pending_release, branch="master"), 7)
    b.ok()

    b.step("release [{:s}.{:s}.{:s}] has been merged into [develop]".format(
        next_major, next_minor, next_build
    ))
    b.checkout("develop")
    if not b.is_merged(pending_release):
        b.exit(NOT_MERGED.format(release=pending_release, branch="develop"), 7)
    b.checkout("master")
    b.ok()

    b.step("tag release [{:s}.{:s}.{:s}]".format(
        next_major, next_minor, next_build
    ))
    b.git_tag()
    b.ok()

    b.step("push [master]")
    b.git_push_tag()
    b.ok()

    b.step("push [develop]")
    b.checkout("develop")
    b.git_push_tag()
    b.checkout("master")
    b.ok()

    b.step("remove obsolete branch [{}]".format(pending_release))
    b.remove_branch(pending_release)
    b.ok()

    print()


def find_webapps(folder):
    for path, directories, filenames in os.walk(folder):
        pkg_json_file = os.path.join(path, "package.json")
        if os.path.exists(pkg_json_file):
            try:
                pkg_json = json.load(
                    open(pkg_json_file, "r", encoding="utf-8"))
            except:
                warn("failed to parse {}", pkg_json_file)
            else:
                if "core4" in pkg_json:
                    command = pkg_json["core4"].get(
                        "build_command", None)
                    dist = pkg_json["core4"].get(
                        "dist", None)
                    if command is not None and dist is not None:
                        yield {
                            "base": path,
                            "command": command,
                            "dist": dist,
                            "name": pkg_json.get("name", None)
                        }


def max_modtime(folder):
    ret = {}
    for path, directories, filenames in os.walk(folder):
        for filename in filenames:
            fn = os.path.join(folder, path, filename)
            fname = pathlib.Path(fn)
            ret[fn] = datetime.datetime.fromtimestamp(fname.stat().st_mtime)
    return ret


def dist(purge=True, dryrun=False, quiet=False):
    def po(*args, **kwargs):
        if not quiet:
            print(*args, **kwargs)

    curdir = os.path.abspath(os.curdir)
    manifest = set()
    po(curdir)
    uptodate = True
    for webapp in find_webapps(curdir):
        po("build", webapp.get("name", None))
        base_path = os.path.abspath(os.path.join(webapp["base"]))
        dist_path = os.path.abspath(
            os.path.join(webapp["base"], webapp["dist"]))
        last_dist = max_modtime(dist_path)
        mx_time = None
        for filename, mtime in max_modtime(base_path).items():
            if filename not in last_dist:
                mx_time = max(mtime, mx_time or mtime)
        if last_dist:
            mx_dist = max(last_dist.values())
            po("latest change inside/outside\n  {}:\n    {} {} {}".format(
                os.path.join(webapp["base"], webapp["dist"]), mx_dist,
                ">" if mx_dist > mx_time else "<", mx_time))
        if os.path.exists(dist_path):
            if (not dryrun) and (not last_dist or mx_dist < mx_time or purge):
                po("purge", dist_path)
                shutil.rmtree(dist_path)
        if not os.path.exists(dist_path) or not last_dist or mx_dist < mx_time:
            for cmd in webapp["command"]:
                os.chdir(webapp["base"])
                po("$ {}".format(cmd))
                uptodate = False
                if not dryrun:
                    cmd = Popen(cmd, shell=True, stderr=STDOUT, stdout=PIPE,
                                close_fds=True, encoding="utf-8")
                    ret = cmd.wait()
                    if ret != 0:
                        po("ERROR!")
                        po(cmd.stdout.read())
                    else:
                        if os.path.exists(webapp["dist"]):
                            manifest.add(dist_path)
                os.chdir(curdir)
        else:
            po("nothing to do")
    manifest_file = find_manifest()
    if not dryrun and manifest_file:
        dirname = os.path.dirname(manifest_file) + os.path.sep
        with open(manifest_file, "r", encoding="utf-8") as fh:
            body = fh.read().split("\n")
        for dist in manifest:
            relpath = dist[len(dirname):]
            include = "recursive-include {}/ *".format(relpath)
            if include not in body:
                po("add {} to MANIFEST".format(relpath))
                body.append(include)
        with open(manifest_file, "w", encoding="utf-8") as fh:
            fh.write("\n".join(body))
    return uptodate


def find_manifest():
    path = os.path.abspath(os.curdir).split(os.path.sep)
    while True:
        if not path:
            break
        curdir = os.path.sep.join(path)
        manifest = os.path.join(curdir, MANIFEST)
        if os.path.exists(manifest):
            return manifest
        path.pop(-1)
    return None


def cran():
    print("install R packages")
    from rpy2.robjects.packages import importr, isinstalled
    if not os.path.exists(R_REQUIREMENTS):
        print("  {} not found".format(R_REQUIREMENTS))
        return False
    rlib = os.path.abspath(os.path.join(os.path.dirname(sys.executable), RLIB))
    if not os.path.isdir(rlib):
        os.makedirs(rlib)
        print("  {} created".format(rlib))
    with open(R_REQUIREMENTS, 'r') as file:
        data = file.read()
    packages_required = data.split(sep='\n')
    utils = importr('utils')
    utils.chooseCRANmirror(ind=0)
    for package in packages_required:
        if package:
            if not isinstalled(package, lib_loc=rlib):
                print("  install", package)
                utils.install_packages(
                    package, lib=rlib, verbose=False, quiet=True)
            else:
                print("  requirement", package, "already satisfied")
