# -*- coding: utf-8 -*-

import os
import sys
import unittest
import tests.util
import pymongo

import core4.base
# import core4.logger
import core4.base.collection
import core4.error


class TestBase(unittest.TestCase):

    def setUp(self):
        dels = []
        for k in os.environ:
            if k.startswith('CORE4_'):
                dels.append(k)
        for k in dels:
            del os.environ[k]
        self.mongo.drop_database('core4test')
        os.environ[
            "CORE4_OPTION_mongo_url"] = "mongodb://core:654321@localhost:27017"
        os.environ["CORE4_OPTION_mongo_database"] = "core4test"
        os.environ["CORE4_CONFIG"] = tests.util.asset("base/local.yaml")

    @property
    def mongo(self):
        return pymongo.MongoClient('mongodb://core:654321@localhost:27017')

    def test_base(self):
        b = core4.base.CoreBase()
        self.assertEqual("core4.base.main.CoreBase", b.qual_name())
        self.assertEqual("core4.base.main.CoreBase", b.qual_name(short=False))

    def test_plugin(self):
        import plugin.test
        t = plugin.test.Test()
        self.assertEqual("plugin", t.plugin)
        self.assertEqual("plugin.test.Test", t.qual_name())
        self.assertEqual("core4.plugin.plugin.test.Test", t.qual_name(
            short=False))
        self.assertEqual("plugin.test.Test()", repr(t))

    def test_plugin_conf(self):
        import plugin.test
        t = plugin.test.Test()
        self.assertTrue(t.plugin_conf().endswith("core4/plugin/plugin.yaml"))
        self.assertEqual(t.config.mongo_database, "core4test")
        self.assertEqual(repr(t), "plugin.test.Test()")
        #self.assertIn("/core4test/sys.role", t.config.sys.role.info_url)
        # self.assertEqual(test, t.config)

    def test_main(self):
        import plugin.test
        from subprocess import check_output
        environ = os.environ
        if "PYTHONPATH" in os.environ:
            pp = os.environ["PYTHONPATH"].split(":")
        else:
            pp = []
        pp.append(os.path.dirname(core4.__file__) + "/..")
        os.environ["PYTHONPATH"] = ":".join(pp)
        out = check_output([sys.executable, plugin.test.__file__], env=environ)
        self.assertEqual(out.decode("utf-8").strip(),
                         'core4.base.main.CoreBase plugin.test.Test')

    def test_collection_scheme(self):
        os.environ["CORE4_OPTION_logging__mongodb"] = "INFO"
        coll1 = core4.base.collection.CoreCollection(
            scheme="mongodb",
            hostname="localhost:27017",
            database="core4test",
            collection="sys.log",
            username="core",
            password="654321"
        )

        class LogOn(core4.base.CoreBase, core4.logger.CoreLoggerMixin):

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.setup_logging()

        a = LogOn()
        a.logger.info("hello world")
        self.assertEqual(coll1.count(), 1)

        self.assertRaises(core4.error.Core4ConfigurationError,
                          lambda: core4.base.collection.CoreCollection(
                              scheme="mongoxxx",
                              hostname="localhost:27017",
                              database="core4test",
                              collection="sys.log",
                              username="core",
                              password="654321"
                          ))
        # pprint(a.config)


if __name__ == '__main__':
    unittest.main()
