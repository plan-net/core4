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


def make_plugin(package_name=None):
    """
    Interactive method used by :mod:`.coco` to create a new plugin.
    The plugin templates are located in directory ``/template``. A combination
    of :mod:`Jinja2` and file-/folder name substitution is used to create a
    new plugin from this blueprint.

    :param package_name: str
    """
    kwargs = {
        "package_name": package_name,
        "package_description": "",
        "package_version": "0.0.1"
    }
    if kwargs["package_name"] and not kwargs["package_name"].isidentifier():
        print("this is not a valid package name")
        sys.exit(1)
    print()
    print("core4 plugin creation")
    print("=====================")
    if kwargs["package_name"] is None:
        kwargs["package_name"] = input_loop("Name: ", identifier=True)
    else:
        print("Name:", kwargs["package_name"])
    kwargs["package_description"] = input_loop("Description: ")
    print()
    while True:
        i = input("type [yes] to continue or press CTRL+C: ")
        if i.strip().lower() == "yes":
            break

    if os.path.exists(kwargs["package_name"]):
        print("\nplugin exists")
        sys.exit(1)
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
            with open(fullsource, "r", encoding="utf-8") as fh:
                body = fh.read()
            Template(body).stream(**kwargs).dump(fulltarget)
            print("created", fulltarget)
    print("done.")