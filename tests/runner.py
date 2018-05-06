"""
This core4 test runner executes each test script located in the same
directory as the script itself. In contrast to Python standard unittest
execution with `python -m unittest discover` this runner executes each
test script in isolation by starting a new Python interpreter process.

See for example https://github.com/cztomczak/pycef/blob/master/unittests/_runner.py
for a similar approach.
"""

import collections
import datetime
import io
import itertools
import os
import re
import subprocess
import sys
import tempfile
import time

Result = collections.namedtuple('Result', 'package tests runtime exit_code '
                                          'output')
PROGRESS = itertools.cycle('┃/━\\')
HEAD_LINE = "  {:40s} {:16s} {:5s}"
REPORT_LINE = "  {:40s} {:16s} {:5d}"
TOTAL_LINE = "  {:>40s} {:16s} {:5d}\n"


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
            yield pkg


def run(logfile, pkg):
    t0 = datetime.datetime.now()
    cmd = ["python", "-m", "unittest", "-v", "-f", "tests." + pkg]
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
    sys.stdout.write("\033[?25l")
    headline("core4 isolated regression tests")
    logfile = tempfile.mktemp()
    result = []

    ret = None
    for pkg in discover():
        ret = run(logfile, pkg)
        result.append(ret)
        if ret.exit_code:
            print("[ FAILED ]\n")
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
    sys.stdout.write("\033[?25h")
    os.unlink(logfile)
    if ret and ret.exit_code:
        print("tests FAIL ({})".format(ret.package))
        raise SystemExit(ret.exit_code)
    print("tests SUCCEED")


if __name__ == '__main__':
    main()
