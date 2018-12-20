import os
import sys

from jinja2 import Template


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
        "package_version": "0.0.1"
    }
    if kwargs["package_name"] and not kwargs["package_name"].isidentifier():
        print("this is not a valid package name")
        sys.exit(1)
    print()
    print("core4 project creation")
    print("=====================")
    if kwargs["package_name"] is None:
        kwargs["package_name"] = input_loop("Name: ", identifier=True)
    else:
        print("Name:", kwargs["package_name"])
    if kwargs["package_description"] is None:
        kwargs["package_description"] = input_loop("Description: ")
    else:
        print("Description:", kwargs["package_description"])
    print()
    while not auto and True:
        i = input("type [yes] to continue or press CTRL+C: ")
        if i.strip().lower() == "yes":
            break
    sys.exit(1)
    # if os.path.exists(kwargs["package_name"]):
    #     print("\nproject exists")
    #     sys.exit(1)
    print()
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
            print("%s " % (fulltarget), end="")
            if os.path.exists(fulltarget):
                print("skipped")
            else:
                with open(fullsource, "r") as fh:
                    body = fh.read()
                Template(body).stream(**kwargs).dump(fulltarget)
                print("created")
    print("done.")
