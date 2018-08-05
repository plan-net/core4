# -*- coding: utf-8 -*-

"""
This core4 test runner executes each test script located in the same
directory as the script itself. In contrast to Python standard unittest
execution with `python -m unittest discover` this runner executes each
test script in isolation by starting a new Python interpreter process.

See for example
https://github.com/cztomczak/pycef/blob/master/unittests/_runner.py for
a similar approach.
"""

import collections
import io
import itertools
import os
import re
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from subprocess import PIPE

import argparse
import datetime
import time

Result = collections.namedtuple('Result', 'package tests runtime exit_code '
                                          'output')
PROGRESS = itertools.cycle('|/━\\')
HEAD_LINE = "  {:40s} {:16s} {:5s}"
REPORT_LINE = "  {:40s} {:16s} {:5d}"
TOTAL_LINE = "  {:>40s} {:16s} {:5d}"

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--coverage", help="run test coverage",
                    action="store_true")
parser.add_argument("-s", "--start", help="test script starts with filter",
                    action="store_true")
parser.add_argument("-m", "--match", help="test script matches filter",
                    action="store_true")
parser.add_argument("filter", help="test script filter",
                    action="store", nargs="?")
args = parser.parse_args()

if args.match and args.start:
    raise SyntaxError("--match and --start are exclusive options")
if args.match or args.start:
    if args.filter is None:
        raise SyntaxError("--match and --start require argument")


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


@contextmanager
def warn():
    if istty():
        print(Colors.WARNING)
    yield
    if istty():
        print(Colors.ENDC)


def line():
    print(HEAD_LINE.format("-" * 40, "-" * 16, "-" * 5))


def headline(s):
    print("\n" + s)
    print("=" * len(s) + "\n")


def discover():
    path = os.path.abspath(os.path.dirname(sys.argv[0]))
    for test in sorted(os.listdir(path)):
        if test.startswith('test_') and test.endswith('.py'):
            (pkg, ext) = os.path.splitext(test)
            if args.start and test.startswith(args.filter):
                yield pkg
            elif args.match and re.match(args.filter, test):
                yield pkg
            elif not (args.start or args.match):
                yield pkg


def istty():
    return os.isatty(sys.stdout.fileno())


def run(logfile, pkg):
    t0 = datetime.datetime.now()
    if args.coverage:
        cmd = ["coverage", "run", "--append", "--source", "core4", "-m",
               "unittest", "-v", "-f", "tests." + pkg]
    else:
        cmd = [sys.executable, "-m", "unittest", "-v", "-f", "tests." + pkg]
    fmt = " " + pkg + (53 - len(pkg)) * " "
    output = ""
    with io.open(logfile, 'w', encoding='utf-8') as writer, io.open(
            logfile, 'r', encoding='utf-8') as reader:
        process = subprocess.Popen(cmd, stdout=writer, stderr=writer)
        while process.poll() is None:
            delta = datetime.datetime.now() - t0
            delta = delta - datetime.timedelta(
                microseconds=delta.microseconds)
            pro = next(PROGRESS) + fmt + "[{:>8s}]\r".format(str(delta))
            if istty():
                sys.stdout.write(pro)
                sys.stdout.flush()
            buf = reader.read()
            output += buf
            time.sleep(0.1)
        buf = str(reader.read())
        output += buf
        exit_code = process.returncode
        print(" ", pkg, end=(53 - len(pkg)) * " ")
    found = re.search('Ran (\d+) tests? in .+?(OK|FAILED)', output,
                      flags=re.DOTALL)
    if found:
        found = int(found.groups()[0])
    else:
        found = 0
    return Result(
        exit_code=exit_code,
        package=pkg,
        runtime=datetime.datetime.now() - t0,
        tests=found,
        output=output
    )


def main():
    if istty():
        sys.stdout.write("\033[?25l")

    try:
        if args.coverage:
            headline("core4 test coverage")
            cmd = ["coverage", "erase"]
            pre_proc = subprocess.Popen(cmd)
            pre_proc.wait()
            if pre_proc.returncode != 0:
                raise SystemExit(pre_proc.returncode)
        else:
            headline("core4 isolated regression tests")
        logfile = tempfile.mktemp()
        result = []

        ret = None
        for pkg in discover():
            ret = run(logfile, pkg)
            result.append(ret)
            if ret.exit_code:
                print("[ FAILED ]\n")
                with warn():
                    headline("DETAILS on failed {}".format(ret.package))
                    print(ret.output)
                break
            else:
                print("[   OK   ]")

        headline("regression test results")
        print(HEAD_LINE.format('test script', 'runtime', 'tests'))
        line()
        for test in result:
            print(REPORT_LINE.format(
                test.package, str(test.runtime), test.tests))
        line()
        runtime = sum([r.runtime.total_seconds() for r in result])
        tests = sum([r.tests for r in result])
        print(TOTAL_LINE.format(
            'total', str(datetime.timedelta(seconds=runtime)), tests))
        os.unlink(logfile)
    finally:
        if istty():
            sys.stdout.write("\033[?25h")

    if ret and ret.exit_code:
        with warn():
            print("tests FAIL ({})".format(ret.package))
        raise SystemExit(ret.exit_code)

    if args.coverage:
        cmd = ["coverage", "report", "-m"]
        post_proc = subprocess.Popen(cmd, stdout=PIPE)
        post_proc.wait()
        if post_proc.returncode != 0:
            raise SystemExit(post_proc.returncode)
        headline("test coverage report")
        print("  ", end="")
        output = post_proc.stdout.read().decode().strip()
        print("\n  ".join(output.splitlines()))

    print("\ntests SUCCEED")


if __name__ == '__main__':
    main()
