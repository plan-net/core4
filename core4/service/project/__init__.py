import os
import sys
import sh
import tempfile
import core4.base.main

from venv import EnvBuilder
from jinja2 import Template

VENV = ".venv"
REPOSITORY = ".repos"


def input_loop(message, identifier=False):
    while True:
        i = input(message).strip()
        if i != "":
            if (not identifier) or (i.isidentifier()):
                return i
            elif identifier:
                print("this is not a valid package name\n")


def make_project(package_name=None, package_description=None, auto=False):
    """
    Interactive method used by :mod:`.coco` to create a new project.
    The project templates are located in directory ``/template``. A combination
    of :mod:`Jinja2` and file-/folder name substitution is used to create a
    new project from this blueprint.

    :param package_name: str
    """
    kwargs = {
        "package_name": package_name,
        "package_description": package_description,
        "package_version": "0.0.1",
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
    core4_home = os.path.abspath(
        os.path.join(core4.base.main.CoreBase.project_path(), '..'))
    if os.path.exists(full_path):
        exist = "WARNING! The directory exists. Missing project files will " \
                "be created. All\n    existing files will not be touched."
    else:
        exist = "The directory does not exists and will be created. All " \
                "project files will\n    be created."
    print("""
    A project directory ./{project:s} will be created at
        > {fullpath:s}
    
    {exist:s}

    Inside this project directory, a Python virtual environment will be created 
    if it does not exist, yet at
        > {venv:s}/{project:s}
    
    Inside this project directory a bare git repository will be created if it
    does not exist, yet at
        > {repository:s}

    This repository will have an initial commit and two branches:
        1. master
        2. develop
        
    To share this git repository with other users you have to manually 
    synchronise this bare repository with a git repository accessible by your
    team. Once this has been done, you can remove the bare repository on this
    computer and update your git connection accordingly in 
        > .git/config
        
    To start working on your project, enter the Python virtual environment with
        $ cd ./{project:s}
        $ . start_env
        
    This will add core4 package via the $PYTHONPATH variable and core4 scripts
    via the $PATH variable:
    
        > PYTHONPATH=$PYTHONPATH:{core4_home:s}
        > PATH=$PATH:{core4_home:s}/{venv:s}/core4/bin
    """.format(
        root=root_path, project=kwargs["package_name"], venv=VENV,
        repository=REPOSITORY, exist=exist, fullpath=full_path,
        core4_home=core4_home))

    while not auto and True:
        i = input("type [yes] to continue or press CTRL+C: ")
        if i.strip().lower() == "yes":
            break

    print("\nbare git repository")
    print("-------------------\n")
    repos_path = os.path.join(full_path, REPOSITORY)

    initial_commit = False
    temp_repos_path = None
    if not os.path.exists(repos_path):

        temp_path = tempfile.mkdtemp()
        temp_repos_path = os.path.join(temp_path, REPOSITORY)
        print("    %s ... " %(temp_repos_path), end="")
        os.makedirs(temp_repos_path)
        sh.git(["init", "--shared", "--bare", temp_repos_path])
        print("created")

        print("    clone into %s ... " %(full_path), end="")
        sh.git(["clone", "file://%s" % (temp_repos_path), full_path])
        print("done")

        initial_commit = True
    else:
        print("    clone %s ... skipped" %(repos_path))

    print("\ncopy files")
    print("----------\n")
    template = os.path.join(os.path.dirname(__file__), "template")
    for root, dirs, files in os.walk(template):
        targetpath = root[len(template):].replace(
            "__name__", kwargs["package_name"])
        if targetpath.startswith("/"):
            targetpath = targetpath[1:]
        targetpath = os.path.join(kwargs["package_name"], targetpath)
        if not os.path.exists(targetpath):
            os.mkdir(targetpath)
        for file in files:
            targetfile = file.replace("__name__", kwargs["package_name"])
            targetfile = targetfile.replace("__py__", "py")
            fulltarget = os.path.join(targetpath, targetfile)
            fullsource = os.path.join(root, file)
            print("    %s ... " % (os.path.abspath(fulltarget)), end="")
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

        print("    intial commit ... ", end="")
        sh.git(git_dir + ["add", "*"])
        sh.git(git_dir + ["commit", ".", "-m", "initial commit"])
        sh.git(git_dir + ["push"])
        print("done")

        print("    create branch develop ... ", end="")
        sh.git(git_dir + ["checkout", "-b", "develop"])
        sh.git(git_dir + ["push", "origin", "develop"])
        sh.git(git_dir + ["branch", "--set-upstream-to", "origin/develop",
                          "develop"])
        sh.git(git_dir + ["checkout", "master"])
        print("done")

        print("    move %s to %s ... " %(temp_repos_path, full_path), end="")
        sh.mv(temp_repos_path, full_path + "/")
        print("done")

        print("    move origin to %s  ... " %(repos_path), end="")
        sh.git(git_dir + ["remote", "set-url", "origin",
                          "file://" + repos_path])
        print("done")

    venv = os.path.join(full_path, VENV, kwargs["package_name"])
    if not os.path.exists(venv):

        print("\nPython virtual environment")
        print("--------------------------\n")

        print("    create at %s ... " %(venv), end="")

        builder = EnvBuilder(system_site_packages=False, clear=False,
                             symlinks=False, upgrade=False, with_pip=True)
        builder.create(venv)
        print("done")
