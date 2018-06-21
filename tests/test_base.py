# -*- coding: utf-8 -*-

import os
import unittest

import core4.base
import core4.logger

os.environ["CORE4_OPTION_mongo_url"] = "mongodb://core:654321@localhost:27017"


class TestRootBase(unittest.TestCase):

    # def test_something(self):
    #     import time
    #     time.sleep(1)
    #     self.assertEqual(True, True)

    def test_base(self):
        b = core4.base.CoreBase()
        self.assertEqual("core4.base.main.CoreBase", b.qual_name())

    def test_plugin(self):
        import plugin.test
        t = plugin.test.Test()
        self.assertEqual("plugin", t.account)
        self.assertEqual("plugin", t.section)
        self.assertEqual("core4.account.plugin.test.Test", t.qual_name())
        self.assertEqual("core4.account.plugin.test.Test", t.qual_name(
            short=False))
        self.assertEqual("plugin.test.Test", t.qual_name(
            short=True))
        b = core4.base.CoreBase()
        self.assertEqual("core4", b.account)
        self.assertEqual("core4", b.section)
        self.assertEqual("core4.base.main.CoreBase", b.qual_name())
        self.assertEqual("core4.base.main.CoreBase", b.qual_name(
            short=False))
        self.assertEqual("core4.base.main.CoreBase", b.qual_name(
            short=True))

    def test_logging(self):
        import plugin.test
        t = plugin.test.Test()
        t.logger.info('hello world')

        class App(core4.base.CoreBase, core4.logger.CoreLoggerMixin):
            pass

        app = App()
        app.start_logging()

    def test_plugin_conf(self):
        import plugin.test
        t = plugin.test.Test()
        self.assertEqual(1, t.config.getint('a', 'plugin.test'))
        self.assertEqual("core4.account.plugin.test.Test()", repr(t))
        b = core4.base.CoreBase()
        self.assertEqual("core4.base.main.CoreBase()", repr(b))
        self.assertEqual(t.identifier, id(t))


if __name__ == '__main__':
    unittest.main()
