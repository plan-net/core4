"""
cadmin - core4 administration and rollout utililty.

Usage:
  cadmin --deploy PROJECT REPOSITORY

Options:
  -d --deploy     deploy project
  -h --help       Show this screen.
"""

CORE4_REMOTE = "git+ssh://git.bi.plan-net.com/srv/git/core4.git@master"


import sys

# ensure this is python3
version = float("%d.%d" % (sys.version_info.major, sys.version_info.minor))
if version < 3.5:
    raise Exception("Must be using Python 3.5 or higher.\n"
                    "This is Python %s" % (version))

import importlib
import os
import venv

try:
    from pip import main as pipmain
except:
    from pip._internal import main as pipmain


def imp(mod):
    try:
        importlib.import_module(mod)
    except:
        print("[{}] not installed... installing it now.".format(mod))
        pipmain(["install", mod])


script = sys.argv[0]
try:
    project = sys.argv[1]
    remote = sys.argv[2]
except:
    raise AttributeError("usage: deploy.py PROJECT REPOSITORY")

python_executable = os.path.abspath(os.path.join(project, "bin", "python"))
upgrade_script = os.path.abspath(
    os.path.join(project, "bin", "requirements.txt"))
if not os.path.exists(python_executable):
    print("install Python virtual environment in [{}]".format(project))
    builder = venv.EnvBuilder(system_site_packages=False, clear=False,
                              symlinks=False, upgrade=False, with_pip=True)
    builder.create(project)

if len(sys.argv) == 3:
    os.execl(
        python_executable, python_executable, script, project, remote, "x")
else:
    print("entering Python virtual environment in [{}]".format(project))
    print("installing [{}] from [{}]".format(project, remote))
    with open(upgrade_script, "w", encoding="utf-8") as fh:
        fh.write("git+" + remote + "\n")
        fh.write(CORE4_REMOTE + "\n")
    pipmain(["install", "--requirement", upgrade_script])
