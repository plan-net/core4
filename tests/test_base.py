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

    #     self.assertEqual("core4.account.plugin.Test", a.logger_name)
    #     b = core4.base.CoreBase()
    #     self.assertEqual("core4.base.main.CoreBase", b.logger_name)
    #     a.logger.info('hello world 1')
    #     b.logger.info('hello world 2')
    #
    #     class App(core4.base.CoreBase, core4.logger.CoreLoggerMixin):
    #         pass
    #
    #     app = App()
    #     app.start_logging()
    #     a.logger.info('hello world 3')
    #     b.logger.info('hello world 4')
    #
    # def test_debug(self):
    #     b = core4.base.CoreBase()
    #     self.assertEqual("core4.base.main.CoreBase", b.logger_name)
    #
    #     class App(core4.base.CoreBase, core4.logger.CoreLoggerMixin):
    #         pass
    #
    #     app = App()
    #     app.start_logging()
    #     b.logger.info('hello world 3')
    #     b.logger.debug('hello debug world 3')
    #     b.logger.warning('hello warning world 3')
    #     b.logger.error('hello error world 3')
    #     b.logger.critical('hello critical world 3')
    #
    # def test_qualname(self):
    #     a = plugin.Test()
    #     self.assertEqual("plugin.Test()", repr(a))
    #     self.assertTrue('plugin.section' in a.config.sections())
    #     self.assertEqual("this is important", a.config.get("message"))
    #     self.assertEqual(103, len(a.config.get("note")))
    #
    # def test_identifier(self):
    #     a = plugin.Test()
    #     print(a.identifier)

if __name__ == '__main__':
    unittest.main()
