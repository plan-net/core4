#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Implements the function :func:`make_project` to create and setup a new core4
project.
"""

import os
import subprocess
import sys
import tempfile
from venv import EnvBuilder

import sh
from jinja2 import Template

import core4.base.main
from core4.const import VENV, REPOSITORY


def input_loop(message, identifier=False):
    while True:
        i = input(message).strip()
        if i != "":
            if (not identifier) or (i.isidentifier()):
                return i
            elif identifier:
                print("this is not a valid package name\n")


def printout(*args):
    print(*args, end="")
    sys.stdout.flush()


def make_project(package_name=None, package_description=None, auto=False,
                 origin=None):
    """
    Interactive method used by :mod:`.coco` to create a new project.
    The project templates are located in directory ``/template``. A combination
    of :mod:`Jinja2` and file-/folder name substitution is used to create a
    new project from this blueprint. A Python virtual environment is created
    installing core4 package using core4 configuration ``core4_origin``.

    :param package_name: str
    :param package_description: str
    :param auto: bool (default ``False``) to skip confirmation
    """
    kwargs = {
        "package_name": package_name,
        "package_description": package_description,
        "package_version": "0.0.0",
    }
    if kwargs["package_name"] and not kwargs["package_name"].isidentifier():
        print("this is not a valid package name")
        sys.exit(1)
    print()
    print("core4 project creation")
    print("======================")
    if kwargs["package_name"] is None:
        kwargs["package_name"] = input_loop("Name: ", identifier=True)
    else:
        print("Name:", kwargs["package_name"])
    if kwargs["package_description"] is None:
        kwargs["package_description"] = input_loop("Description: ")
    else:
        print("Description:", kwargs["package_description"])
    root_path = os.path.abspath(".")
    full_path = os.path.join(root_path, kwargs["package_name"])
    kwargs["full_path"] = full_path
    kwargs["venv"] = VENV
    if os.path.exists(full_path):
        exist = "WARNING! The directory exists. Missing project files will " \
                "be created. All\n    existing files will not be touched."
    else:
        exist = "The directory does not exists and will be created. All " \
                "project files will\n    be created."

    base = core4.base.main.CoreBase()
    core4_repository = origin or base.config.core4_origin

    print("""
    A project directory ./{package_name:s} will be created at
        > {full_path:s}

    {exist:s}

    Inside this project directory, a Python virtual environment will be created 
    if it does not exist, yet at
        > {venv:s}

    This Python virtual environment hosts core4 from {core4_repository:s}.

    Inside this project directory a bare git repository will be created if it
    does not exist, yet at
        > {repository:s}

    This repository will have an initial commit and two branches:
        1. master
        2. develop

    To share this git repository with other users you have to manually 
    synchronise this bare repository with a git repository accessible by your
    team. Once this has been done, you can remove the bare repository on this
    computer.

    To start working on your project, enter the Python virtual environment with
        $ cd ./{package_name:s}
        $ source enter_env

    To exit the Python virtual environment type
        $ deactivate        
    """.format(
        root=root_path, package_name=kwargs["package_name"], venv=VENV,
        repository=REPOSITORY, exist=exist, full_path=full_path,
        core4_repository=core4_repository))

    while not auto and True:
        i = input("type [yes] to continue or press CTRL+C: ")
        if i.strip().lower() == "yes":
            break

    print("\nbare git repository")
    print("-------------------\n")
    repos_path = os.path.join(full_path, REPOSITORY)

    initial_commit = False
    temp_repos_path = None
    git_path = os.path.join(full_path, ".git")
    if not os.path.exists(git_path):
        if not os.path.exists(repos_path):
            temp_path = tempfile.mkdtemp()
            temp_repos_path = os.path.join(temp_path, REPOSITORY)
            printout("    %s ... " % (temp_repos_path))
            os.makedirs(temp_repos_path)
            sh.git(["init", "--shared", "--bare", temp_repos_path])
            print("created")

            printout("    clone into %s ... " % (full_path))
            sh.git(["clone", "file://%s" % (temp_repos_path), full_path])
            print("done")

            initial_commit = True
        else:
            print("    clone %s ... skipped" % (repos_path))
    else:
        curr_dir = os.path.abspath(os.path.curdir)
        os.chdir(os.path.abspath(os.path.dirname(git_path)))
        origin_url = None
        for line in sh.git("config", "--list").split("\n"):
            if line.startswith("remote.origin.url="):
                origin_url = line[len("remote.origin.url="):]
                break
        os.chdir(curr_dir)
        print("    git origin %s ... exists" % (origin_url))

    print("\ncopy files")
    print("----------\n")
    template = os.path.join(os.path.dirname(__file__), "template")
    for root, dirs, files in os.walk(template):
        targetpath = root[len(template):].replace(
            "__name__", kwargs["package_name"])
        if targetpath.startswith("/"):
            targetpath = targetpath[1:]
        if targetpath.endswith("__pycache__"):
            continue
        targetpath = os.path.join(kwargs["package_name"], targetpath)
        if not os.path.exists(targetpath):
            os.mkdir(targetpath)
        for file in files:
            targetfile = file.replace("__name__", kwargs["package_name"])
            targetfile = targetfile.replace("__py__", "py")
            fulltarget = os.path.join(targetpath, targetfile)
            fullsource = os.path.join(root, file)
            printout("    %s ... " % (os.path.abspath(fulltarget)))
            if os.path.exists(fulltarget):
                print("skipped")
            else:
                with open(fullsource, "r") as fh:
                    body = fh.read()
                Template(body).stream(**kwargs).dump(fulltarget)
                print("created")

    if initial_commit:
        print("\ninitial commit")
        print("--------------\n")

        git_dir = ["--git-dir", os.path.join(full_path, ".git"),
                   "--work-tree", full_path]

        printout("    initial commit ... ")
        sh.git(git_dir + ["add", "*"])
        sh.git(git_dir + ["commit", ".", "-m", "initial commit"])
        sh.git(git_dir + ["push"])
        print("done")

        printout("    create branch develop ... ")
        sh.git(git_dir + ["checkout", "-b", "develop"])
        sh.git(git_dir + ["push", "origin", "develop"])
        sh.git(git_dir + ["branch", "--set-upstream-to", "origin/develop",
                          "develop"])
        sh.git(git_dir + ["checkout", "master"])
        print("done")

        printout("    move %s to %s ... " % (temp_repos_path, full_path))
        sh.mv(temp_repos_path, full_path + "/")
        print("done")

        printout("    move origin to %s  ... " % (repos_path))
        sh.git(git_dir + ["remote", "set-url", "origin",
                          "file://" + repos_path])
        print("done")

    venv = os.path.join(full_path, VENV)
    if not os.path.exists(venv):
        print("\nPython virtual environment")
        print("--------------------------\n")

        printout("    create at %s ... " % (venv))
        builder = EnvBuilder(system_site_packages=False, clear=False,
                             symlinks=False, upgrade=False, with_pip=True)
        builder.create(venv)
        print("done")

        pip_cmd = sh.Command(os.path.join(venv, "bin", "pip"))

        printout("    upgrade pip ... ")
        pip_cmd(["install", "-U", "pip"])
        print("done")

        printout("    install project ... ")
        pip_cmd(["install", "-e", full_path])
        print("done")

        printout("    install core4 ... ")
        pip_cmd(["install", core4_repository])
        # if ret != 0:
        #     raise ConnectionError("failed to retrieve and install core4 "
        #                           "from %s" % (core4_repository))
        print("done")
