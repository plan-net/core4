"""
cadmin - core4 administration utililty.



Usage:
  cadmin --project
  cadmin --version

Options:
  -h --help       Show this screen.
  -v --version    Show version.
"""

from docopt import docopt

import core4
import core4.base.main
import core4.service.introspect.project

base = core4.base.main.CoreBase()


def list_project():
    pf = core4.service.introspect.project.CorePortfolio()
    for (name, path, binary) in pf.list_project():
        print(name)
        print(pf.enter_project(name, binary))


def main():
    args = docopt(__doc__, help=True, version=core4.__version__)
    if args["--project"]:
        list_project()
    else:
        raise SystemExit("nothing to do.")


if __name__ == '__main__':
    import sys

    sys.argv.append("--project")
    main()
