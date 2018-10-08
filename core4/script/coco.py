"""
coco - core control utililty.

Usage:
  coco --project [PROJECT]
  coco --halt
  coco --worker [IDENTIFIER]
  coco --enqueue QUAL_NAME [ARGS]...
  coco (--pause | --resume) [PROJECT]
  coco --version

Options:
  -e --enqueue  enqueue job
  -w --worker   launch worker
  -x --halt     immediate system halt
  -h --help     Show this screen.
  -v --version  Show version.
"""

import json
import re

from docopt import docopt

import core4
import core4.logger.mixin
import core4.queue.main
import core4.queue.worker
import core4.service.project


def halt():
    print("system halt")
    core4.queue.main.CoreQueue().halt(now=True)


def worker(name):
    core4.logger.mixin.logon()
    w = core4.queue.worker.CoreWorker(name=name)
    print("start worker [%s]" % (w.identifier))
    w.start()


def pause(project):
    q = core4.queue.main.CoreQueue()
    if not q.maintenance(project):
        print("entering maintenance", end="")
        q.enter_maintenance(project)
    else:
        print("in maintenance already,\nnothing to do", end="")
    if project:
        print(" on [%s]" % (project))
    else:
        print()


def resume(project):
    q = core4.queue.main.CoreQueue()
    if q.maintenance(project):
        print("leaving maintenance", end="")
        q.leave_maintenance(project)
    else:
        print("not in maintenance,\nnothing to do", end="")
    if project:
        print(" on [%s]" % (project))
    else:
        print()


def enqueue(qual_name, *args):
    print("enqueueing [%s]" % (qual_name))
    if args:
        cmdline = []
        for a in args:
            cmdline.append(
                re.sub(r"^\s*(\w+)\s*[\:\=]\s*(.+)\s*$", r'"\1": \2', a))
        js = "{%s}" % (", ".join(cmdline))
        try:
            data = json.loads(js)
        except:
            if len(args) == 1:
                data = json.loads(args[0])
            else:
                s = str(args)
                raise json.JSONDecodeError("failed to parse %s" % (s), s, 0)
    else:
        data = {}
    q = core4.queue.main.CoreQueue()
    q.enqueue(name=qual_name, **data)


def project(name):
    core4.service.project.make_project(name)


def main():
    args = docopt(__doc__, help=True, version=core4.__version__)
    if args["--halt"]:
        halt()
    elif args["--worker"]:
        worker(args["IDENTIFIER"])
    elif args["--pause"]:
        pause(args["PROJECT"])
    elif args["--resume"]:
        resume(args["PROJECT"])
    elif args["--enqueue"]:
        enqueue(args["QUAL_NAME"], *args["ARGS"])
    elif args["--project"]:
        project(args["PROJECT"])
    else:
        raise SystemExit("nothing to do.")
    print("done.")


if __name__ == '__main__':
    main()
