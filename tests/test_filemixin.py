# -*- coding: utf-8 -*-

import os
import shutil
import unittest
from core4.queue.job import CoreJob
from core4.queue.file import FileMixin
import re
import tests.util


class TestBase(unittest.TestCase):

    MAGIC_NR_GZIP = '1f8b'

    def setUp(self):
        self.baseroot = "/tmp/core4.testing"

        os.environ["CORE4_OPTION_folder__root"] = self.baseroot
        os.environ["CORE4_OPTION_process_directory"] = self.baseroot + "/proc"
        os.environ["CORE4_OPTION_folder__archive_skip_compress"] = "skip"

        if os.path.exists(self.baseroot):
            shutil.rmtree(self.baseroot, ignore_errors=False)

        os.makedirs(self.baseroot)

        # project will get overwriten when executing locally without calling runner.py
        self.project = 'tests'
        self.tester = TestFile()
        self.tester.project = 'tests'

    def tearDown(self):
        tests.util.drop_env()

    def test_list_proc(self):
        with self.assertRaises(RuntimeError):
            self.tester.list_proc()
        os.makedirs(self.baseroot + "/proc")
        os.makedirs(self.baseroot + "/proc/tests")
        self.assertEqual(self.tester.list_proc(), self.baseroot + "/proc/tests")
        self.assertEqual(self.tester.list_proc(pattern=re.compile(".*")), list())
        open(self.baseroot + "/proc/tests/testfile", 'a').close()
        self.assertEqual(self.tester.list_proc(pattern=re.compile('.*')), [self.baseroot
                                                                           + '/proc/tests/testfile'])
        open(self.baseroot + "/proc/tests/pattern_testfile1", 'a').close()
        open(self.baseroot + "/proc/tests/pattern_testfile2", 'a').close()
        self.assertEqual(self.tester.list_proc(pattern=re.compile('pattern_*')),
                         [self.baseroot + '/proc/tests/pattern_testfile1',
                          self.baseroot + '/proc/tests/pattern_testfile2'])
        self.assertEqual(self.tester.list_proc(pattern=re.compile('pattern not present*')), list())


    def test_move_proc(self):

        with self.assertRaises(RuntimeError):
            self.tester.move_proc('/tmp/test_move_not_present')

        open('/tmp/test_move', 'a').close()

        with self.assertRaises(RuntimeError):
            self.tester.move_proc('/tmp/test_move')

        os.makedirs(self.baseroot + "/proc")

        self.tester.move_proc("/tmp/test_move")
        self.assertEqual(self.tester.list_proc(pattern=re.compile(".*")),
                         [self.baseroot + "/proc/tests/test_move"])

        open('/tmp/test_move', 'a').close()
        with self.assertRaises(RuntimeError):
            self.tester.move_proc('/tmp/test_move', overwrite=False)

        self.tester.move_proc('/tmp/test_move', overwrite=True)
        self.assertEqual(self.tester.list_proc(pattern=re.compile(".*")),
                         [self.baseroot + "/proc/tests/test_move"])

    @unittest.skip
    def test_move_arch(self):

        with self.assertRaises(RuntimeError):
            self.tester.move_arch(source='/tmp/test_move_arch_not_present')

        open('/tmp/test_move_arch', 'a').close()

        with self.assertRaises(RuntimeError):
            self.tester.move_arch('/tmp/test_move_arch')

        os.makedirs(self.baseroot + "/arch")
        os.makedirs(self.baseroot + "/arch/tests")

        self.tester.move_arch("/tmp/test_move_arch", compress=False)
        self.assertEqual(os.listdir(self.baseroot + "/arch/tests/None"),
                         ["test_move_arch"])
        open('/tmp/test_move_arch_compressed', 'a').close()
        self.tester.move_arch("/tmp/test_move_arch_compressed", compress=True)
        self.assertEqual(os.listdir(self.baseroot + "/arch/tests/None"),
                         ["test_move_arch", "test_move_arch_compressed.gz"])

        with open(self.baseroot + "/arch/tests/None/test_move_arch_compressed.gz", 'rb') as f:
            self.assertEqual((f.read()[:2]).hex(), self.MAGIC_NR_GZIP)

        open('/tmp/test_move_arch_compressed', 'a').close()

        with self.assertRaises(RuntimeError):
            self.tester.move_arch('/tmp/test_move_arch_compressed', compress=True)

    def test_list_transfer(self):
        with self.assertRaises(RuntimeError):
            self.tester.list_transfer()

        os.makedirs(self.baseroot + "/transfer")
        os.makedirs(self.baseroot + "/transfer/tests")

        self.assertEqual(self.tester.list_transfer(), self.baseroot + "/transfer/tests")
        self.assertEqual(self.tester.list_transfer(pattern=re.compile(".*")), list())
        open(self.baseroot + "/transfer/tests/testfile", 'a').close()
        self.assertEqual(self.tester.list_transfer(pattern=re.compile('.*')), [self.baseroot
                                                                           + '/transfer/tests/testfile'])
        open(self.baseroot + "/transfer/tests/pattern_testfile1", 'a').close()
        open(self.baseroot + "/transfer/tests/pattern_testfile2", 'a').close()
        self.assertEqual(self.tester.list_transfer(pattern=re.compile('pattern_*')),
                         [self.baseroot + '/transfer/tests/pattern_testfile1',
                          self.baseroot + '/transfer/tests/pattern_testfile2'])
        self.assertEqual(self.tester.list_transfer(pattern=re.compile('pattern not present*')), list())


class TestFile(CoreJob, FileMixin):
    def test(self):
        pass


if __name__ == '__main__':
    unittest.main(exit=False)
