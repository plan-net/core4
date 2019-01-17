"""
chist - core4 log history

Usage:
  chist [--start=START] [--end=END] [--level=LEVEL] [--project=PROJECT]
      [--hostname=HOSTNAME] [--username=USERNAME] [--qual_name=QUAL_NAME]
      [--identifier=ID] [--message=PATTERN] [--follow] [SECONDS] [--tab]

Options:
  -s --start=START          lower timestamp boundary
  -e --end=END              upper timestamp boundary
  -l --level=LEVEL          log level filter
  -p --project=PROJECT      project filter
  -h --hostname=HOSTNAME    hostname filter
  -u --username=USERNAME    username filter
  -q --qual_name=QUAL_NAME  qual_name filter
  -i --identifier=ID        object identifier filter
  -m --message=PATTERN      message regular expression filter
  -f --follow               follow log message interval
  -t --tab                  tab seperated
  -h --help                 Show this screen.
"""

import logging
import re
import sys

from datetime import datetime, time, timedelta
from docopt import docopt

import core4
import core4.util.data
from core4.base.main import CoreBase

LOG_LEVEL = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


def parse_datetime(value):
    match = re.split("\D", value)
    parts = ["%Y", "%m", "%d", "%H", "%M", "%S"]
    if match:
        fmt = " ".join(parts[:len(match)])
        txt = " ".join(match)
        try:
            dt = datetime.strptime(txt, fmt)
        except:
            pass
        else:
            return dt
    return None


def parse_time(value):
    match = re.split("\D", value)
    parts = ["%H", "%M", "%S"]
    if match:
        fmt = " ".join(parts[:len(match)])
        txt = " ".join(match)
        try:
            return datetime.strptime(txt, fmt).time()
        except:
            pass
    return None


def parse_delta(value):
    match = re.match("^\s*(.+?)\s*([hdwm])\s*$", value, flags=re.IGNORECASE)
    if match:
        number = float(match.groups()[0])
        metric = match.groups()[1].lower()
        if metric in "hdw":
            if metric == "h":
                delta = number
            elif metric == "d":
                delta = number * 24.
            elif metric == "w":
                delta = number * 24. * 7.
            return timedelta(hours=delta)
    return None


def parse_datetime_range(start, end, today=None):
    if today is None:
        today = datetime.now()
    current_time = today.time()

    def _parse_range(value):
        if value is not None:
            for parse in [parse_datetime, parse_time, parse_delta]:
                p = parse(value)
                if p is not None:
                    return p
        return None

    start = _parse_range(start)
    end = _parse_range(end)

    if start is None:
        if end is not None:
            raise ValueError("end requires start")
        return None, None

    start_type = type(start)
    end_type = type(end)
    left = None
    right = None

    if start_type is time:
        if end_type is datetime:
            raise ValueError("invalid date/time range: time - datetime")
        start = datetime(today.year, today.month, today.day,
                         start.hour, start.minute, start.second)
        if start.time() >= current_time:
            left = start - timedelta(days=1)
        else:
            left = start
        if end_type is time:
            right = datetime(left.year, left.month, left.day,
                             end.hour, end.minute, end.second)
            if right < left:
                right += timedelta(days=1)
    elif start_type is datetime:
        left = start
        if end_type is time:
            right = datetime(left.year, left.month, left.day,
                             end.hour, end.minute, end.second)
            if right < left:
                right += timedelta(days=1)
        elif end_type is datetime:
            right = end
    elif start_type is timedelta:
        left = today - start
        if end_type is time:
            right = datetime(left.year, left.month, left.day,
                             end.hour, end.minute, end.second)
            if right < left:
                right += timedelta(days=1)
        elif end_type is datetime:
            right = end
        elif end_type is timedelta:
            right = left + end
    if end_type is timedelta:
        right = left + end
    if right is not None:
        if not (start_type is datetime
                or end_type is datetime
                or start_type is timedelta):
            if right >= today or left >= today:
                left -= timedelta(days=1)
                right -= timedelta(days=1)
        if right < left:
            raise ValueError("invalid date/time range: end < start")
    return left, right


def build_query(args, clock=None, utc=True):
    query = []
    # --start and --end
    start = args.get("--start", None)
    end = args.get("--end", None)
    if not (start or end):
        start = "1h"
    left, right = parse_datetime_range(start, end, today=clock)
    if left:
        if utc:
            left = core4.util.data.local2utc(left)
        query.append({"created": {"$gte": left}})
    if right:
        if utc:
            right = core4.util.data.local2utc(right)
        query.append({"created": {"$lt": right}})
    # exact match --hostname and --username
    for search in ("hostname", "username"):
        value = args.get("--" + search, None)
        if value is not None:
            query.append({search: value})
    # --level
    level = args.get("--level", None)
    if level:
        found = False
        for test in LOG_LEVEL:
            if test.startswith(level.upper()):
                query.append({"levelno": {"$gte": getattr(logging, test)}})
                found = True
                break
        if not found:
            sys.exit("unknown --level")
    # left match: --project and --qual_name
    for search in ("project", "qual_name"):
        value = args.get("--" + search, None)
        if value is not None:
            query.append({search: re.compile("^" + value + "\..+")})
    # right match: --identifier
    identifier = args.get("--identifier", None)
    if identifier:
        query.append({"identifier": re.compile("^.*" + identifier + "$")})
    # message
    message = args.get("--message", None)
    if message:
        query.append({"message": re.compile(message)})

    return query


def main(args, clock=None):
    query = build_query(args, clock)
    base = CoreBase()
    cur = base.config.sys.log.find(
        filter={"$and": query}, sort=[("created", 1), ("_id", 1)])

    def printout(*args, **kwargs):
        print(*args, **kwargs, end="")

    for doc in cur:
        if args["--tab"]:
            print("\t".join([
                str(core4.util.data.utc2local(doc["created"])),
                doc["level"],
                "{}@{}".format(doc["username"], doc["hostname"]),
                "{}@{}".format(doc["qual_name"], doc["identifier"]),
                doc["message"]]), end="")
            if "exception" in doc:
                out = "".join(doc["exception"]["text"])
                print(out)
            else:
                print()
        else:
            printout("{:>19s} ".format(str(core4.util.data.utc2local(
                doc["created"]))))
            printout("{:<8s} ".format(doc["level"]))
            printout("{}@{} ".format(doc["username"], doc["hostname"]))
            printout("{}@{}: ".format(doc["qual_name"], doc["identifier"]))
            print(doc["message"])
            if "exception" in doc:
                out = "".join(doc["exception"]["text"])
                print("|", "\n| ".join(out.split("\n")))
    print(query)


if __name__ == '__main__':
    main(args=docopt(__doc__, help=True, version=core4.__version__))
