"""coco - core control utililty.

Usage:
  coco (-e --enqueue <JOB>)
  coco (--project [NAME])
  coco (-h | --help)
  coco (-v | --version)

Options:
  -h --help     Show this screen.
  -v --version  Show version.
"""

from docopt import docopt
import core4
import core4.service.project


def version():
    print("core4, version [{}]".format(core4.__version__))

def make_project():
    core4.service.project.make_project()

def main():
    args = docopt(__doc__)
    if args["--version"]:
        version()
    elif args["--project"]:
        core4.service.project.make_project(args["NAME"])
    else:
        print("unknown", args)

if __name__ == '__main__':
    main()