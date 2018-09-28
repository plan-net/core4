"""coco - core control utililty.

Usage:
  coco (--plugin [NAME])
  coco (-h | --help)
  coco (-v | --version)

Options:
  -h --help     Show this screen.
  -v --version  Show version.
"""

from docopt import docopt
import core4
import core4.service.plugin


def version():
    print("core4, version [{}]".format(core4.__version__))

def make_plugin():
    core4.service.plugin.make_plugin()

def main():
    args = docopt(__doc__)
    if args["--version"]:
        version()
    elif args["--plugin"]:
        core4.service.plugin.make_plugin(args["NAME"])
    else:
        print("unknown", args)

if __name__ == '__main__':
    main()