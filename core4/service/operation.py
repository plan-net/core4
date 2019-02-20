#This Source Code Form is subject to the terms of the Mozilla Public
#License, v. 2.0. If a copy of the MPL was not distributed with this
#file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import re
import sys
import textwrap

import sh

import core4.util.node
from core4.base.main import CoreBase

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
                    nums = re.split("\D", match.groups()[0])
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

    (_, next_major, next_minor, next_build) = re.split("\D+", pending_release)

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
