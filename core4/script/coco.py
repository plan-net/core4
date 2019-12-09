#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
coco - core4 control utililty.

Use coco to interact with the core4 backend and frontend in the areas of

* project management
* setup control
* maintenance
* job management
* daemon control (worker, scheduler, application server)
* release management

Usage:
  coco --init [PROJECT] [DESCRIPTION] [--yes]
  coco --halt
  coco --worker [IDENTIFIER]
  coco --application [IDENTIFIER] [--routing=ROUTING] [--port=PORT] \
[--address=ADDRESS] [--project=PROJECT] [--filter=FILTER]...
  coco --scheduler [IDENTIFIER]
  coco --alive
  coco --enqueue QUAL_NAME [ARGS]...
  coco --info
  coco --listing [STATE]...
  coco --detail (ID | QUAL_NAME)...
  coco --remove (ID | QUAL_NAME)...
  coco --remove-hard (ID | QUAL_NAME)...
  coco --restart [ID | QUAL_NAME]...
  coco --kill [ID | QUAL_NAME]...
  coco (--pause | --resume) [PROJECT]
  coco --mode
  coco --build
  coco --release
  coco --who
  coco --jobs [--introspect]
  coco --home
  coco --container
  coco --version

Options:
  -e --enqueue     enqueue job
  -w --worker      launch worker
  -s --scheduler   launch scheduler
  -a --alive       worker alive/dead state
  -i --info        job state summary
  -l --listing     job listing
  -d --detail      job details
  -x --halt        immediate system halt
  -h --help        show this screen.
  -v --version     show version.
  -o --who         show system information
  -j --jobs        enumerate available jobs
  -n --introspect  register available jobs in sys.job
  -c --container   enumerate available API container
  -m --home        enumerate available core4 projects in home folder
  -y --yes         Assume yes on all requests.
"""

import datetime
import json
import re
from pprint import pprint

from bson.objectid import ObjectId
from docopt import docopt

import core4
import core4.api.v1.tool
import core4.api.v1.tool.functool
import core4.error
import core4.logger.mixin
import core4.queue.helper.functool
import core4.queue.job
import core4.queue.main
import core4.queue.scheduler
import core4.queue.worker
import core4.service.introspect.main
import core4.service.project
import core4.util.data
import core4.util.node
from core4.service.operation import build, release

QUEUE = core4.queue.main.CoreQueue()


def halt():
    print("system halt")
    QUEUE.halt(now=True)


def worker(name):
    core4.logger.mixin.logon()
    w = core4.queue.worker.CoreWorker(name=name)
    print("start worker [%s]" % (w.identifier))
    w.start()


def app(**kwargs):
    core4.logger.mixin.logon()
    kwargs["debug"] = False
    core4.api.v1.tool.functool.serve_all(**kwargs)


def scheduler(name):
    core4.logger.mixin.logon()
    w = core4.queue.scheduler.CoreScheduler(name=name)
    print("start scheduler [%s]" % (w.identifier))
    w.start()


def alive():
    rec = []
    mx = 0
    cols = ["loop", "loop_time", "heartbeat", "kind", "_id"]
    for doc in QUEUE.get_daemon():
        mx = max(0, len(doc["_id"]))
        doc["loop"] = doc["loop"].replace(microsecond=0)
        for t in ("loop_time", "heartbeat"):
            doc[t] = datetime.timedelta(seconds=int(doc[t].total_seconds()))
        rec.append([str(doc[k]) for k in cols])
    if rec:
        print("{:19s} {:19s} {:19s} {:9s} {:s}".format(*cols))
        print(" ".join(["-" * i for i in [19, 19, 19, 9, mx]]))
    else:
        print("no daemon.")
    for doc in rec:
        print("{:19s} {:19s} {:19s} {:9s} {:s}".format(*doc))


def info():
    rec = []
    mx = 0
    for doc in QUEUE.get_queue_state():
        rec.append(doc)
        mx = max(mx, len(doc["name"]))
    if rec:
        print("{:>6s} {:8s} {:4s} {:s}".format(
            "n", "state", "flag", "name"
        ))
        print(" ".join(["-" * i for i in [6, 8, 4, mx]]))
    else:
        print("no jobs.")
    for doc in rec:
        print(
            "{:6d}".format(doc["n"]),
            "{:8.8s}".format(doc["state"]),
            "{:4.4s}".format(doc["flags"]),
            "{:s}".format(doc["name"])
        )


def listing(*state):
    filter = []
    for s in list(state):
        s = s.lower().strip()
        if s in [
            core4.queue.job.STATE_PENDING,
            core4.queue.job.STATE_RUNNING,
            core4.queue.job.STATE_DEFERRED,
            core4.queue.job.STATE_FAILED,
            core4.queue.job.STATE_INACTIVE,
            core4.queue.job.STATE_ERROR,
            core4.queue.job.STATE_KILLED
        ]:
            if s not in filter:
                filter.append(s)
        else:
            print("unknown state [%s]" % (s))
            raise SystemExit
    kwargs = {}
    if filter:
        kwargs["state"] = {
            "$in": filter
        }
    rec = []
    mx = 0
    mxworker = 6
    for job in QUEUE.get_job_listing(**kwargs):
        mx = max(mx, len(job["name"]))
        if job["locked"]:
            mxworker = max(mxworker, len(job["locked"]["worker"]))
        rec.append(job)
    if rec:
        fmt = "{:24s} {:8s} {:4s} {:>4s} {:4s} {:7s} {:6s} " \
              "{:19s} {:19s} {:11s} {:%d} {:s}" % (
                  mxworker)
        print(
            fmt.format(
                "_id", "state", "flag", "pro", "prio", "attempt", "user",
                "enqueued", "age", "runtime", "worker", "name"))
        print(" ".join(["-" * i
                        for i in
                        [24, 8, 4, 4, 4, 7, 6, 19, 19, 11, mxworker, mx]]))
    else:
        print("no jobs.")
    fmtworker = "{:%ds}" % (mxworker)
    for job in rec:
        locked = job["locked"]
        progress = job.get("prog", {}).get("value", 0)
        if locked:
            worker = job["locked"]["worker"]
        else:
            worker = ""
        if job["state"] == core4.queue.job.STATE_RUNNING:
            job["attempts_left"] -= 1
        flag = "".join([k[0].upper() if job[k] else "." for k in
                        ["zombie_at", "wall_at", "removed_at", "killed_at"]])
        if job["state"] == "running":
            addon = core4.util.node.mongo_now() - job["started_at"]
            runtime = addon.total_seconds()
        else:
            runtime = job["runtime"] or 0
        runtime = datetime.timedelta(seconds=int(runtime))
        age = core4.util.node.mongo_now() - (
                job["enqueued"]["at"] or core4.util.node.mongo_now()
        )
        age = datetime.timedelta(seconds=int(age.total_seconds()))
        print(
            job["_id"],
            "{:8.8s}".format(job["state"]),
            "{:4.4s}".format(flag),
            "{:3.0f}%".format(100. * (progress or 0.)),
            "{:03d}{:1s}".format(job["priority"], "F" if job.get(
                "force", False) else " "),
            "{:3d}/{:3d}".format(
                job["attempts"] - job["attempts_left"], job["attempts"]),
            "{:<6.6s}".format(job.get("enqueued", {}).get("username", None)),
            "{:19s}".format(core4.util.data.utc2local(
                job["enqueued"]["at"]).strftime("%Y-%m-%d %H:%M:%S")),
            "{:19s}".format(str(age)),
            "{:11s}".format(str(runtime)),
            fmtworker.format(worker),
            job["name"]
        )


def _handle(_id, call):
    _id = list(_id)
    while _id:
        i = _id.pop(0)
        try:
            oid = ObjectId(i)
        except:
            for job in QUEUE.get_job_listing(name=i):
                _id.append(job["_id"])
        else:
            yield oid, call(oid)


def remove(*_id):
    for (oid, ret) in _handle(set(_id), QUEUE.remove_job):
        if ret:
            print("removed [{}]".format(oid))
        else:
            print("failed to remove [{}]".format(oid))


def remove_hard(*_id):
    for (oid, ret) in _handle(set(_id), QUEUE.remove_hard):
        if ret:
            print("hard removed [{}]".format(oid))
        else:
            print("failed to hard remove [{}]".format(oid))


def restart(*_id):
    for (oid, ret) in _handle(set(_id), QUEUE.restart_job):
        if ret:
            print("restarted [{}], new  _id [{}]".format(oid, ret))
        else:
            print("failed to restart [{}]".format(oid))


def kill(*_id):
    for (oid, ret) in _handle(set(_id), QUEUE.kill_job):
        if ret:
            print("killed [{}]".format(oid))
        else:
            print("failed to kill [{}]".format(oid))


def detail(*_id):
    _id = list(_id)
    while _id:
        i = _id.pop(0)
        try:
            oid = ObjectId(i)
        except:
            for job in QUEUE.get_job_listing(name=i):
                _id.append(job["_id"])
                break
        else:
            pprint(QUEUE.job_detail(oid))
            print("-" * 80)
            stdout = QUEUE.get_job_stdout(oid)
            print("STDOUT:\n" + str(stdout))
            break


def pause(project):
    if not QUEUE.maintenance(project):
        print("entering maintenance", end="")
        QUEUE.enter_maintenance(project)
    else:
        print("in maintenance already,\nnothing to do", end="")
    if project:
        print(" on [%s]" % (project))
    else:
        print()


def resume(project):
    if QUEUE.maintenance(project):
        print("leaving maintenance", end="")
        QUEUE.leave_maintenance(project)
    else:
        print("not in maintenance,\nnothing to do", end="")
    if project:
        print(" on [%s]" % (project))
    else:
        print()


def mode():
    print("global maintenance:")
    print(" ", QUEUE.maintenance())
    project = QUEUE.maintenance(project=True)
    if project:
        print("project maintenance:")
        for p in project:
            print(" ", p)


def enqueue(qual_name, *args):
    print("enqueueing [%s]" % (qual_name[0]))
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
    job_id = core4.queue.helper.functool.enqueue(qual_name[0], **data)
    print(job_id)


def init(name, description, yes):
    core4.service.project.make_project(name, description, yes)


def jobs(introspect=False):
    intro = core4.service.introspect.main.CoreIntrospector()
    if introspect:
        intro.collect_job()
    seen = set()
    for project in intro.retrospect():
        if project["name"] not in seen:
            print(project["name"])
            for job in sorted([j["name"] for j in project["jobs"]]):
                print("  " + job)
            seen.add(project["name"])


def container():
    intro = core4.service.introspect.main.CoreIntrospector()
    seen = set()
    for project in intro.introspect():
        if project["name"] not in seen:
            print(project["name"], "-", project["version"])
            for api in sorted(project["api_containers"],
                              key=lambda r: r["name"]):
                print("  {} ({})".format(api["name"], api["root"]))
                for rule in api["rules"]:
                    print("    {} ({})".format(rule[1], rule[0]))
            seen.add(project["name"])


def who():
    intro = core4.service.introspect.main.CoreIntrospector()
    summary = intro.summary()
    print("USER:")
    print("  {:s} IN {}".format(summary["user"]["name"],
                                ", ".join(summary["user"]["group"])))
    print("UPTIME:")
    print("  {} ({:1.0f} sec.)".format(summary["uptime"]["text"],
                                       summary["uptime"]["epoch"]))
    print("PYTHON:")
    print("  {} {}".format(summary["python"]["executable"],
                           summary["python"]["version"]))
    print("CONFIGURATION:")
    print("  {}".format(
        "\n  ".join(
            ("file://" + f for f in summary["config"]["files"])
        )
    ))
    if summary["config"]["database"]:
        print("  mongodb://{}".format(summary["config"]["database"]))
    print("MONGODB:")
    print("  {}".format(summary["database"]))
    print("DIRECTORIES:")
    for k in ("home", "transfer", "process", "archive", "temp"):
        print("  {:<9s} {}".format(k + ":", summary["folder"][k]))
    print("DAEMONS:")
    have = False
    for daemon in summary["daemon"]:
        print("  {kind:s}: {_id:s} (pid: {pid:d})".format(**daemon))
        have = True
    if not have:
        print("  none.")


def home():
    intro = core4.service.introspect.main.CoreIntrospector()
    seen = set()
    for project in intro.introspect():
        if project["name"] not in seen:
            print(
                "{} - {} ({}) with Python {}, pip {}, core4 - {} ({})".format(
                    project["name"],
                    project["version"],
                    project["build"],
                    project["python_version"],
                    project["pip"],
                    project["core4_version"],
                    project["core4_build"]
                ))
            seen.add(project["name"])


def main():
    args = docopt(__doc__, help=True, version=core4.__version__)
    if args["--halt"]:
        halt()
    elif args["--worker"]:
        worker(args["IDENTIFIER"])
    elif args["--application"]:
        app(name=args["IDENTIFIER"], port=args["--port"],
            project=args["--project"], filter=args["--filter"],
            routing=args["--routing"], address=args["--address"])
    elif args["--scheduler"]:
        scheduler(args["IDENTIFIER"])
    elif args["--pause"]:
        pause(args["PROJECT"])
    elif args["--resume"]:
        resume(args["PROJECT"])
    elif args["--enqueue"]:
        enqueue(args["QUAL_NAME"], *args["ARGS"])
    elif args["--init"]:
        init(args["PROJECT"], args["DESCRIPTION"], args["--yes"])
    elif args["--alive"]:
        alive()
    elif args["--info"]:
        info()
    elif args["--listing"]:
        listing(*args["STATE"])
    elif args["--remove"]:
        remove(*args["ID"])
    elif args["--remove-hard"]:
        remove_hard(*args["ID"])
    elif args["--restart"]:
        restart(*args["ID"])
    elif args["--kill"]:
        kill(*args["ID"])
    elif args["--detail"]:
        detail(*args["ID"])
    elif args["--mode"]:
        mode()
    elif args["--build"]:
        build()
    elif args["--release"]:
        release()
    elif args["--who"]:
        who()
    elif args["--jobs"]:
        jobs(args["--introspect"])
    elif args["--home"]:
        home()
    elif args["--container"]:
        container()
    else:
        raise SystemExit("nothing to do.")


if __name__ == '__main__':
    main()
