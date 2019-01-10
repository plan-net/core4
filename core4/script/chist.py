"""
chist - core4 log history

Usage:
  chist [--start <START>] [--end <END>] [--level <LEVEL>] [--project <PROJECT>] [--host <HOSTNAME>] [--user <USER>] [--name <NAME>] [--identifier <IDENTIFIER>] [--regex <REGEX>] [--follow [SECONDS]]

Options:
  -s --start       lower timestamp boundary
  -e --end         upper timestamp boundary
  -l --level       log level filter
  -p --project     project filter
  -h --host        hostname filter
  -u --user        username filter
  -n --name        qual_name filter
  -i --identifier  object identifier filter
  -r --regex       message regular expression filter
  -f --follow      follow log message interval
  -h --help        Show this screen.
"""

import datetime
import re

import time
from docopt import docopt

import core4
from core4.base.main import CoreBase
import core4.util.data


def parse_datetime(value, utc=False, *args, **kwargs):
    match = re.split("\D", value)
    parts = ["%Y", "%m", "%d", "%H", "%M", "%S"]
    if match:
        fmt = " ".join(parts[:len(match)])
        txt = " ".join(match)
        try:
            dt = datetime.datetime.strptime(txt, fmt)
        except:
            pass
        else:
            if utc or len(match) <= 3:
                return dt
            utc_struct_time = time.gmtime(time.mktime(dt.timetuple()))
            return datetime.datetime.fromtimestamp(
                time.mktime(utc_struct_time))
    return None


def get_now(now, utc):
    if now is None:
        if utc:
            return datetime.datetime.utcnow()
        else:
            return datetime.datetime.now()
    return now


def parse_time(value, utc=False, now=None, *args, **kwargs):
    match = re.split("\D", value)
    parts = ["%H", "%M", "%S"]
    if match:
        fmt = " ".join(parts[:len(match)])
        txt = " ".join(match)
        now = get_now(now, utc)
        try:
            dt = datetime.datetime.strptime(txt, fmt)
        except:
            return None
        ret = datetime.datetime(now.year, now.month, now.day, dt.hour,
                                dt.minute, dt.second)
        if ret > now:
            ret -= datetime.timedelta(days=1)
        if utc:
            return ret
        utc_struct_time = time.gmtime(time.mktime(ret.timetuple()))
        return datetime.datetime.fromtimestamp(time.mktime(utc_struct_time))
    return None


def parse_delta(value, utc=False, now=None, sign=-1, *args, **kwargs):
    match = re.match("^\s*(.+?)\s*([hdwm])\s*$", value, flags=re.IGNORECASE)
    if match:
        number = float(match.groups()[0])
        metric = match.groups()[1].lower()
        now = get_now(now, utc)
        if metric in "hdw":
            if metric == "h":
                delta = number
            elif metric == "d":
                delta = number * 24.
            elif metric == "w":
                delta = number * 24. * 7.
            dt = now + sign * datetime.timedelta(hours=delta)
        else:
            if sign == -1:
                if now.month == 1:
                    month = 12
                    year = now.year - 1
                else:
                    month = now.month - 1
                    year = now.year
            else:
                if now.month == 12:
                    month = 1
                    year = now.year + 1
                else:
                    month = now.month + 1
                    year = now.year
            day = now.day
            while True:
                try:
                    dt = datetime.datetime(year, month, day, now.hour,
                                           now.minute, now.second)
                    break
                except ValueError:
                    month += 1
                    if month > 12:
                        year += 1
                        month = 1
                    day = 1
        if utc:
            return dt
        utc_struct_time = time.gmtime(time.mktime(dt.timetuple()))
        return datetime.datetime.fromtimestamp(time.mktime(utc_struct_time))
    return None


def parse_range(value, now=None, utc=False, sign=-1):
    if value is None:
        raise ValueError("expected argument")
    for parse in [parse_datetime, parse_time, parse_delta]:
        p = parse(value, now=now, sign=sign, utc=utc)
        if p is not None:
            return p
    return None


def main():
    args = docopt(__doc__, help=True, version=core4.__version__)
    query = []
    start = None
    utc = False
    print(args)
    import sys
    sys.exit()
    if not (args["--start"] or args["--end"]):
        args["--start"] = True
        args["START"] = "1h"
    if args["--start"]:
        start = parse_range(args["START"])
        utc = True
        query.append({"created": {"$gte": start}})
    if args["--end"]:
        end = parse_range(args["END"], now=start, utc=utc, sign=1)
        query.append({"created": {"$lt": end}})
    if not args["--start"]:
        start = end - datetime.timedelta(hours=3)
        query.append({"created": {"$gte": start}})
    if args["--identifier"]:
        query.append({"identifier": args["IDENTIFIER"]})
    base = CoreBase()
    cur = base.config.sys.log.find(
        filter={"$and": query}, sort=[("created", 1), ("_id", 1)])

    def printout(*args, **kwargs):
        print(*args, **kwargs, end="")

    for doc in cur:
        printout("{:>19s} ".format(str(core4.util.data.utc2local(
            doc["created"]))))
        printout("{:<8s} ".format(doc["level"]))
        printout("{}@{} ".format(doc["username"], doc["hostname"]))
        printout("{}@{}> ".format(doc["qual_name"], doc["identifier"]))
        print(doc["message"])
        if "exception" in doc:
            out = "".join(doc["exception"]["text"])
            print("|", "\n| ".join(out.split("\n")))


if __name__ == '__main__':
    main()
