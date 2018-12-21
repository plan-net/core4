import os
import sys
import re
import sh
import core4.util.node
import textwrap

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
        super().__init__()
        self._project = project
        self._step = False
        self._init_file = None
        self.major = None
        self.minor = None
        self.build = None
        self._body = None
        self._version_line = None
        self._built_line = None

    def is_project(self):
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
                    (self.major, self.minor, self.build) = [int(i) for i in nums]
                    self._version_line = lno
                elif re.match(r"""^__built__\s*\=\s*.+?\s*""", line):
                    self._built_line = lno
            self._body.append(line.strip())
            lno += 1
        fh.close()
        return in_scope

    def pending_release(self):
        for line in sh.git(["branch", "-a", "--no-color"]).split("\n"):
            match = re.match(r"(release-\d+\.\d+\.\d+)", line.strip())
            if match:
                return match.groups()[0]
        return None

    def current_branch(self):
        for line in sh.git(["branch", "--no-color"]).split("\n"):
            if line.strip().startswith("*"):
                return line[2:]
        raise RuntimeError("no branch found")

    def is_clean(self):
        return sh.git(["status", "--porcelain"]) == ""

    def is_merged(self, release):
        for line in sh.git(["branch", "-a", "--no-color", "--merged"]):
            if line.strip() == release.strip():
                return True
        return False

    def has_commits(self, left, right):
        out = sh.git(["rev-list", "--count", "%s..%s" % (left, right)])
        return int(out) > 0

    def get_latest(self):
        return (0, 0, 5)

    def create_release(self, major, minor, num):
        sh.git(["checkout", "-b", "release-%d.%d.%d" % (major, minor, num)])

    def bump(self, major, minor, num):
        sh.git(["commit", ".", "-m", "bump release-%d.%d.%d" % (major, minor, num)])

    def git_push(self, major, minor, num):
        # git push --set-upstream origin release-0.0.3
        sh.git(["push", "--set-upstream", "origin", "release-%d.%d.%d" % (major, minor, num)])

    def git_push_tag(self):
        sh.git(["push"])
        sh.git(["push", "--tags"])

    def step(self, message):
        print("[        ]  {}".format(message), end="\r")
        print("[        ]  ", end="")
        sys.stdout.flush()
        self._step = True

    def ok(self):
        print("\r[   OK   ]")
        self._step = False

    def exit(self, message, code=1):
        if self._step:
            print("\r[ FAILED ]\n")
        print("\n".join(textwrap.wrap(message, 60)))
        print()
        sys.exit(code)

    def headline(self, message):
        print(message)
        print("=" * len(message))
        print()

    def get_number(self, message, default):
        while True:
            print("  %-s [%d] > " % (message, default), end="")
            choice = input()
            if choice.strip() == "":
                choice = str(default)
            if choice.isnumeric():
                return int(choice)

    def mark_release(self, major, minor, num):
        lno = 0
        body = []
        for line in self._body:
            if lno == self._version_line:
                body.append('__version__ = "%d.%d.%d"' %(major, minor, num))
            elif lno == self._built_line:
                body.append('__built__ = "%s"' %(core4.util.node.mongo_now()))
            else:
                body.append(line)
            lno += 1
        fh = open(self._init_file, "w", encoding="utf-8")
        for line in body:
            fh.write("%s\n" %(line))

    def checkout(self, branch):
        sh.git(["checkout", branch])

    def git_tag(self):
        sh.git(["tag", "%d.%d.%d" %(self.major, self.minor, self.build)])

    def remove_branch(self, release):
        sh.git(["branch", "-d", release])
        sh.git(["push", "origin", "--delete", release])


def build():
    project = os.path.basename(os.path.abspath(os.curdir))
    b = CoreBuilder(project)

    print()
    b.headline("CORE4: project [{}] build process".format(project))

    b.step("verify core4 project")
    if not b.is_project():
        b.exit(NO_PROJECT)
    b.ok()

    b.step("no pending release")
    pending_release = b.pending_release()
    if pending_release is not None:
        b.exit(PENDING_RELEASE.format(release=pending_release))
    b.ok()

    b.step("this is branch [develop]")
    branch = b.current_branch()
    if branch != "develop":
        b.exit(NOT_DEVELOP.format(branch=branch))
    b.ok()

    b.step("working tree is clean")
    if not b.is_clean():
        b.exit(NOT_CLEAN.format())
    b.ok()

    b.step("commits exist")
    if not b.has_commits("master", "develop"):
        b.exit(NO_BUILD_COMMITS.format())
    b.ok()

    print()
    b.headline("define next release version")
    print("current local release: [%d.%d.%d]\n" % (b.major, b.minor, b.build))
    # todo: could be that local latest is different to remote latest
    major = b.get_number("major", b.major)
    minor = b.get_number("minor", b.minor)
    num = b.get_number("build", b.build + 1)

    print()
    if (major, minor, num) <= (b.major, b.minor, b.build):
        b.exit("WARNING!\nCurrent release is higher/equal to next release "
               "[%d.%d.%d]. Please update the next release version.")

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
    project = os.path.basename(os.path.abspath(os.curdir))
    b = CoreBuilder(project)

    print()
    b.headline("CORE4: project [{}] release process".format(project))

    b.step("verify core4 project")
    if not b.is_project():
        b.exit(NO_PROJECT)
    b.ok()

    b.step("pending release")
    pending_release = b.pending_release()
    if pending_release is None:
        b.exit(NO_PENDING_RELEASE)
    b.ok()

    b.step("this is branch [master]")
    branch = b.current_branch()
    if branch != "master":
        b.exit(NOT_MASTER.format(branch=branch))
    b.ok()

    b.step("working tree is clean")
    if not b.is_clean():
        b.exit(NOT_CLEAN.format())
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
        b.exit(NOT_MERGED.format(release=pending_release, branch="master"))
    b.ok()

    b.step("release [{:s}.{:s}.{:s}] has been merged into [develop]".format(
        next_major, next_minor, next_build
    ))
    b.checkout("develop")
    if not b.is_merged(pending_release):
        b.exit(NOT_MERGED.format(release=pending_release, branch="develop"))
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


if __name__ == '__main__':
    os.chdir("/tmp/test_project")
    #build()
    release()
