# -*- coding: utf-8 -*-

import os
import sys
import unittest

import pymongo

import core4.base
import core4.base.collection
import core4.config
import core4.config.tag
import core4.error
import tests.util


class MyConfig(core4.config.main.CoreConfig):
    cache = False


class LogOn(core4.base.CoreBase, core4.logger.CoreLoggerMixin):
    config_class = MyConfig

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_logging()

    def make_config(self, *args, **kwargs):
        return MyConfig(*args, **kwargs)


class TestBase(unittest.TestCase):

    def setUp(self):
        dels = []
        for k in os.environ:
            if k.startswith('CORE4_'):
                dels.append(k)
        for k in dels:
            del os.environ[k]
        self.mongo.drop_database('core4test')
        os.environ["CORE4_CONFIG"] = tests.util.asset("base/local.yaml")

    @property
    def mongo(self):
        return pymongo.MongoClient('mongodb://core:654321@localhost:27017')

    def tearDown(self):
        tests.util.drop_env()

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
        self.assertTrue(t.plugin_config().endswith("core4/plugin/plugin.yaml"))
        self.assertEqual(t.config.mongo_database, "core4test")
        self.assertEqual(repr(t), "plugin.test.Test()")
        # self.assertIn("/core4test/sys.role", t.config.sys.role.info_url)
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

        a = LogOn()
        a.logger.info("hello world")
        # data = list(coll1.find())
        # import pandas as pd
        # df = pd.DataFrame(data)
        # print(df.to_string())

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

    def test_progress(self):
        os.environ["CORE4_OPTION_logging__mongodb"] = "INFO"
        bc = LogOn()
        bc.progress(0.01)
        bc.progress(0.04)  # suppress
        bc.progress(0.05)
        bc.progress(0.05)  # suppress
        bc.progress(0.08)
        bc.progress(0.09)  # suppress
        bc.progress(0.12)  # suppress
        data = list(self.mongo.core4test.sys.log.find())
        self.assertEqual(3, len(data))
        for i, check in enumerate([0, 5, 10]):
            self.assertRegex(data[i]["message"], "{}%$".format(check))

    def test_progress_restart(self):
        os.environ["CORE4_OPTION_logging__mongodb"] = "INFO"
        bc = LogOn()
        bc.progress(0.01)
        bc.progress(0.05)
        bc.progress(0.10)
        bc.progress(0.15)
        bc.progress(0.09)
        bc.progress(0.08)  # suppress
        bc.progress(0.50)
        bc.progress(0.10)  # restart
        data = list(self.mongo.core4test.sys.log.find())
        self.assertEqual(7, len(data))
        for i, check in enumerate([0, 5, 10, 15, 10, 50, 10]):
            self.assertRegex(data[i]["message"], "{}%$".format(check))

    def test_custom_progress(self):
        os.environ["CORE4_OPTION_logging__mongodb"] = "INFO"
        bc = LogOn()
        bc.progress(0.01, inc=0.1)
        bc.progress(0.05, inc=0.1)
        bc.progress(0.10, inc=0.1)
        bc.progress(0.15, inc=0.1)
        bc.progress(0.18, inc=0.1)
        bc.progress(0.20, inc=0.1)
        bc.progress(0.22, inc=0.1)
        bc.progress(0.25, inc=0.1)
        bc.progress(0.28, inc=0.1)
        data = list(self.mongo.core4test.sys.log.find())
        self.assertEqual(4, len(data))
        for i, check in enumerate([0, 10, 20, 30]):
            self.assertRegex(data[i]["message"], "{}%$".format(check))

    def test_progress_message(self):
        os.environ["CORE4_OPTION_logging__mongodb"] = "INFO"
        bc = LogOn()
        bc.progress(0.01, "hello %s: %1.2f", "world", 0.01, inc=0.1)
        bc.progress(0.12, "hello %s: %1.2f", "world", 0.12, inc=0.1)
        data = list(self.mongo.core4test.sys.log.find())
        self.assertEqual(2, len(data))
        self.assertEqual(data[0]["message"],
                         "progress at 0% - hello world: 0.01")
        self.assertEqual(data[1]["message"],
                         "progress at 10% - hello world: 0.12")

    # todo: make work
    def _test_unwind_config(self):

        import core4.config.test

        class XConfig(core4.config.test.TestConfig):
            cache = False

        class A(LogOn):
            def make_config(self, *args, **kwargs):
                kwargs["local_dict"] = {
                    "tests": {
                        "test_base": {
                            "A": {
                                "log_level": "WARNING"
                            }
                        }
                    },
                    "sys": {
                        "log": core4.config.tag.ConnectTag(
                            "mongodb://core:654321@localhost:27017"
                            "/core4test/sys.log")
                    },
                    "logging": {
                        "mongodb": "DEBUG"
                    }

                }
                return XConfig(*args, **kwargs)

        a = A()
        self.assertEqual("WARNING", a.config.tests.test_base.A.log_level)
        self.assertEqual("WARNING", a.log_level)
        b = core4.base.CoreBase()
        for o in [a, b]:
            o.logger.debug("this is debug")
            o.logger.info("this is info")
            o.logger.warning("this is warning")
            o.logger.error("this is error")

        coll1 = core4.base.collection.CoreCollection(
            scheme="mongodb",
            hostname="localhost:27017",
            database="core4test",
            collection="sys.log",
            username="core",
            password="654321"
        )
        data = list(coll1.find())
        self.assertEqual(1, sum([1 for i in data if i["level"] == "DEBUG"]))
        self.assertEqual(1, sum([1 for i in data if i["level"] == "INFO"]))
        self.assertEqual(2, sum([1 for i in data if i["level"] == "WARNING"]))
        self.assertEqual(2, sum([1 for i in data if i["level"] == "ERROR"]))

    # todo: move const


if __name__ == '__main__':
    unittest.main()
