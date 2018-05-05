import collections
import datetime
import os
import re
import subprocess
import sys

Result = collections.namedtuple('Result', 'package tests runtime')


def line():
    print("  {:40s} {:16s} {:4s}".format("-" * 40, "-" * 16, "-" * 4))


def headline(s):
    print("\n" + s)
    print("=" * len(s) + "\n")


path = os.path.abspath(os.path.dirname(sys.argv[0]))
result = []

headline("core4 isolated regression tests")
for test in sorted(os.listdir(path)):
    if test.startswith('test_') and test.endswith('.py'):
        (pkg, ext) = os.path.splitext(test)
        t0 = datetime.datetime.now()
        cmd = ["python", "-m", "unittest", "-v", "-f", "tests." + pkg]
        print(" ", pkg, end=(52 - len(pkg)) * " ")
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            exit_code = 0
        except subprocess.CalledProcessError as exc:
            output = exc.output
            exit_code = exc.returncode
        # If tests failed parse output for errors/failures
        output = output.decode()
        if exit_code:
            print("[ FAILED ]\n\nDETAILS:\n\n" + output)
            raise SystemExit(1)
        else:
            print("[   OK   ]")
        found = re.search('Ran (\d+) tests? in .+?OK', output, flags=re.DOTALL)
        result.append(Result(
            package=pkg,
            runtime=datetime.datetime.now() - t0,
            tests=int(found.groups()[0])
        ))

headline("regression test results")
print("  {:40s} {:16s} {:4s}".format('test', 'runtime', 'test'))
line()
runtime = 0
tests = 0
for test in result:
    runtime += test.runtime.total_seconds()
    tests += test.tests
    print("  {:40s} {:16s} {:4d}".format(
        test.package, str(test.runtime), test.tests))
line()
print("  {:>40s} {:16s} {:4d}\n".format(
    'total', str(datetime.timedelta(seconds=runtime)), tests))
