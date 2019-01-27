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
  coco --application [IDENTIFIER] [--routing=ROUTING] [--port=PORT] [--filter=FILTER...]
  coco --scheduler [IDENTIFIER]
  coco --alive
  coco --enqueue QUAL_NAME [ARGS]...
  coco --info
  coco --listing [STATE]...
  coco --detail (ID | QUAL_NAME)...
  coco --remove (ID | QUAL_NAME)...
  coco --restart [ID | QUAL_NAME]...
  coco --kill [ID | QUAL_NAME]...
  coco (--pause | --resume) [PROJECT]
  coco --mode
  coco --build
  coco --release
  coco --who
  coco --jobs
  coco --project
  coco --version

Options:
  -e --enqueue    enqueue job
  -w --worker     launch worker
  -s --scheduler  launch scheduler
  -a --alive      worker alive/dead state
  -i --info       job state summary
  -l --listing    job listing
  -d --detail     job details
  -x --halt       immediate system halt
  -h --help       show this screen.
  -v --version    show version.
  -o --who        show system information
  -j --jobs       enumerate available jobs
  -p --project    enumerate available core4 projects
  -y --yes        Assume yes on all requests.
"""

import json
import re
from pprint import pprint

import datetime
from bson.objectid import ObjectId
from docopt import docopt

import core4
import core4.api.v1.tool
import core4.api.v1.tool.functool
import core4.logger.mixin
import core4.queue.job
import core4.queue.main
import core4.queue.scheduler
import core4.queue.worker
import core4.service.introspect.project
import core4.service.project
import core4.util.data
import core4.util.node
from core4.service.operation import build, release
from core4.service.introspect.command import ENQUEUE_ARG
import core4.service.introspect


QUEUE = core4.queue.main.CoreQueue()


def halt():
    print("system halt")
    QUEUE.halt(now=True)


def worker(name):
    core4.logger.mixin.logon()
    w = core4.queue.worker.CoreWorker(name=name)
    print("start worker [%s]" % (w.identifier))
    w.start()


def app(name, port, filter, routing=None):
    core4.logger.mixin.logon()
    if port:
        port = int(port)
    core4.api.v1.tool.functool.serve_all(name=name, port=port,
                                         filter=filter or None,
                                         routing=routing)


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
        fmt = "{:24s} {:8s} {:4s} {:>4s} {:4s} {:7s} {:6s} {:19s} {:11s} {:11s} {:%d} {:s}" % (
            mxworker)
        print(
            fmt.format(
                "_id", "state", "flag", "pro", "prio", "attempt", "user",
                "enqueued", "age", "runtime", "worker", "name"))
        print(" ".join(["-" * i
                        for i in
                        [24, 8, 4, 4, 4, 7, 6, 19, 11, 11, mxworker, mx]]))
    else:
        print("no jobs.")
    fmtworker = "{:%ds}" % (mxworker)
    for job in rec:
        locked = job["locked"]
        if locked:
            progress = job["locked"]["progress_value"] or 0
            worker = job["locked"]["worker"]
        else:
            progress = 0.
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
        runtime = datetime.timedelta(seconds=runtime)
        print(
            job["_id"],
            "{:8.8s}".format(job["state"]),
            "{:4.4s}".format(flag),
            "{:3.0f}%".format(100. * progress),
            "{:03d}{:1s}".format(job["priority"], "F" if job.get(
                "force", False) else " "),
            "{:3d}/{:3d}".format(
                job["attempts"] - job["attempts_left"], job["attempts"]),
            "{:<6.6s}".format(job.get("enqueued", {}).get("username", None)),
            "{:19s}".format(str(
                core4.util.data.utc2local(job["enqueued"]["at"]))),
            "{:11s}".format(str(core4.util.node.mongo_now() - (
                    job["enqueued"]["at"] or core4.util.node.mongo_now()))),
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
    try:
        job_id = QUEUE.enqueue(name=qual_name[0], **data)._id
    except ImportError:
        stdout = core4.service.introspect.exec_project(
            qual_name[0], ENQUEUE_ARG, qual_name=qual_name[0],
            args="**%s" % (str(data)))
        job_id = stdout
    except:
        raise
    print(job_id)


def init(name, description, yes=False):
    core4.service.project.make_project(name, description, yes)


def jobs():
    intro = core4.service.introspect.CoreIntrospector()
    summary = dict(intro.list_project())
    for project in sorted(summary.keys()):
        print("{}".format(project))
        jobs = []
        for job in summary[project]["job"]:
            job_project = job["name"].split(".")[0]
            if job_project == project:
                jobs.append(job["name"])
        for job in sorted(jobs):
            print("  {}".format(job))


def who():
    intro = core4.service.introspect.CoreIntrospector()
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


def project():
    intro = core4.service.introspect.CoreIntrospector()
    summary = dict(intro.list_project())
    print("PROJECTS:")
    for project in sorted(summary.keys()):
        modules = {}
        if summary[project]:
            for mod in summary[project]["project"]:
                modules[mod["name"]] = mod
            print("  {} ({}) with Python {}, pip {}".format(
                modules[project]["name"], modules[project]["version"],
                summary[project]["python_version"],
                summary[project]["pip"],
            ))
            for mod in sorted(modules.keys()):
                if mod != project:
                    print("    {} ({})".format(
                        modules[mod]["name"], modules[mod]["version"]
                    ))


def main():
    args = docopt(__doc__, help=True, version=core4.__version__)
    if args["--halt"]:
        halt()
    elif args["--worker"]:
        worker(args["IDENTIFIER"])
    elif args["--application"]:
        app(args["IDENTIFIER"], args["--port"], args["--filter"],
            args["--routing"])
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
        jobs()
    elif args["--project"]:
        project()
    else:
        raise SystemExit("nothing to do.")


if __name__ == '__main__':
    main()
