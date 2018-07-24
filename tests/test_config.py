# -*- coding: utf-8 -*-

import os
import unittest
from pprint import pprint
import pymongo
import tests.util
import core4.config
import core4.error
import datetime


os.environ["CORE4_OPTION_mongo_url"] = "mongodb://core:654321@localhost:27017"

class MyConfig(core4.config.CoreConfig):

    _cache = None


class TestConfig(unittest.TestCase):

    def setUp(self):
        dels = []
        for k in os.environ:
            if k.startswith('CORE4_'):
                dels.append(k)
        for k in dels:
            del os.environ[k]
        self.mongo.drop_database('core4test')

    @property
    def mongo(self):
        return pymongo.MongoClient('mongodb://core:654321@localhost:27017')

    def test_eval(self):
        with open(tests.util.asset("config/extra.py"),
                  "r", encoding="utf-8") as f:
            code = f.read()
        globals = {}
        locals = {}
        exec(code, globals, locals)

    def test_illegal(self):
        extra = tests.util.asset("config/extra.py")
        local = tests.util.asset("config/local.py")
        conf = MyConfig(extra_config=extra, config_file=local)
        conf._load()
        #self.assertRaises(KeyError, conf._load)
        #self.assertIsNone(conf._config)
        #print(conf)

    def test_overload(self):
        extra = tests.util.asset("config/extra.py")
        local = tests.util.asset("config/local1.py")
        conf = MyConfig(extra_config=extra, config_file=local)
        conf._load()
        self.assertEqual(1, sum([1 for p in conf.path
                                 if p.endswith("core4/config/core.py")]))
        self.assertEqual(1, sum([1 for p in conf.path
                                 if p.endswith("asset/config/extra.py")]))
        self.assertEqual(1, sum([1 for p in conf.path
                                 if p.endswith("asset/config/local1.py")]))
        self.assertEqual(3, len(conf.path))
        self.assertEqual("from local1", conf._config["mongo_url"])
        conf = MyConfig(extra_config=extra)
        conf._load()
        self.assertEqual(1, sum([1 for p in conf.path
                                 if p.endswith("core4/config/core.py")]))
        self.assertEqual(1, sum([1 for p in conf.path
                                 if p.endswith("asset/config/extra.py")]))
        self.assertEqual("from extra", conf._config["mongo_url"])
        self.assertEqual(2, len(conf.path))

    def test_cascade(self):
        extra = tests.util.asset("config/extra.py")
        local = tests.util.asset("config/local1.py")
        conf = MyConfig(extra_config=extra, config_file=local)
        conf._load()
        conf._cascade()
        self.assertEqual(conf._config["mongo_url"], "from local1")
        self.assertEqual(conf._config["mongo_database"], "core4dev")
        self.assertEqual(conf._config["account1"]["mongo_url"], "from local1")
        self.assertEqual(conf._config["account1"]["mongo_database"], "account-1-database")
        #pprint(conf._config)
        self.assertEqual(conf._config["account2"]["var1"], 1)
        self.assertEqual(conf._config["account2"]["var2"], 2)
        self.assertEqual(conf._config["account2"]["var3"], 333)

    def test_cascade_fail(self):
        extra = tests.util.asset("config/extra.py")
        local = tests.util.asset("config/local2.py")
        conf = MyConfig(extra_config=extra, config_file=local)
        #self.assertRaises(KeyError, conf._load)
        #self.assertIsNone(conf._config)
        #print(conf)

    def test_g(self):
        extra = tests.util.asset("config/extra.py")
        local = tests.util.asset("config/local1.py")
        conf = MyConfig(extra_config=extra, config_file=local)
        self.assertEqual(conf.account1.mongo_url, "from local1")
        self.assertEqual(conf.account1.sys.log, "this no good")
        self.assertEqual(conf.account1["s p"], "service plan")
        self.assertEqual(conf.account1.datetime,
                         datetime.datetime(2018, 1, 14))

    def test_connect(self):
        extra = tests.util.asset("config/extra1.py")
        local = tests.util.asset("config/local3.py")
        conf = MyConfig(extra_config=extra, config_file=local)
        self.assertEqual(conf.mongo_database, "local3db")
        #print(conf.account1.coll1)
        #print(conf.account1.coll2)

    def test_split(self):
        extra = tests.util.asset("config/extra1.py")
        local = tests.util.asset("config/local3.py")
        conf = MyConfig(extra_config=extra, config_file=local)
        c = core4.config.connect(
            "mongodb://user:pwd@testfile:27017/filedb/filecoll1").render(conf)
        self.assertEqual("user@testfile:27017/filedb/filecoll1", c.info_url)
        c = core4.config.connect(
            "mongodb://filedb/filecoll2").render(conf)
        self.assertEqual("admin@local3:27017/filedb/filecoll2", c.info_url)
        c = core4.config.connect(
            "mongodb://filecoll3").render(conf)
        self.assertEqual("admin@local3:27017/local3db/filecoll3", c.info_url)

    def test_malformed(self):
        extra = tests.util.asset("config/extra1.py")
        local = tests.util.asset("config/local3.py")
        conf = MyConfig(extra_config=extra, config_file=local)
        self.assertRaises(
            core4.error.Core4ConfigurationError,
            core4.config.connect(
                "user:pwd@testfile:27017/filedb/filecoll1").render,
            conf
        )
        self.assertRaises(
            core4.error.Core4ConfigurationError,
            core4.config.connect(
                "mongodb://testfile/a/b/c").render,
            conf
        )
        self.assertRaises(
            core4.error.Core4ConfigurationError,
            core4.config.connect(
                "mongodb:/a/b/c").render,
            conf
        )

    def test_use(self):
        extra = tests.util.asset("config/extra2.py")
        local = tests.util.asset("config/local4.py")
        conf = MyConfig(extra_config=extra, config_file=local)
        self.assertEqual(conf.account1.coll1.name, "coll1")
        self.assertEqual(conf.account1.coll1.database, "core4test")
        self.assertEqual(0, conf.account1.coll1.count())
        conf.account1.coll1.insert_one({"name": "test"})
        self.assertEqual(1, conf.account1.coll1.count())
        self.assertEqual(conf.account2.coll1.info_url,
                         "core:654321localhost:27018/extra2db3/coll3")
        self.assertEqual(conf.account2.coll2.info_url,
                         "core:654321localhost:27018/extra2db3/coll5")

    def test_env(self):
        os.environ["CORE4_OPTION_extra_global"] = "777"
        os.environ["CORE4_OPTION_env1__k1"] = "def"
        os.environ["CORE4_OPTION_env1__k2"] = "ok"
        os.environ["CORE4_OPTION_env1__k4"] = ""
        extra = tests.util.asset("config/extra2.py")
        local = tests.util.asset("config/local4.py")
        conf = MyConfig(extra_config=extra, config_file=local)
        self.assertEqual(conf.extra_global, 777)
        self.assertEqual(conf.env1.k1, "def")
        self.assertEqual(conf.env1.k2, "ok")
        self.assertIsNone(conf.env1.k3)
        self.assertIsNone(conf.env1.k4)

    def test_use(self):
        extra = tests.util.asset("config/extra2.py")
        local = tests.util.asset("config/local4.py")
        conf = MyConfig(extra_config=extra, config_file=local)
        self.assertEqual(conf.account1.coll1.name, "coll1")
        self.assertEqual(conf.account1.coll1.database, "core4test")
        self.assertEqual(0, conf.account1.coll1.count())
        conf.account1.coll1.insert_one({"name": "test"})
        self.assertEqual(1, conf.account1.coll1.count())
        self.assertEqual(conf.account2.coll1.info_url,
                         "core:654321localhost:27018/extra2db3/coll3")
        self.assertEqual(conf.account2.coll2.info_url,
                         "core:654321localhost:27018/extra2db3/coll5")
        k = list(conf.keys())
        self.assertTrue("mongo_url" in k)
        self.assertTrue("env1" in k)

    def test_missing(self):
        extra = tests.util.asset("config/extra2.py")
        local = tests.util.asset("config/local5.py")
        conf = MyConfig(extra_config=extra, config_file=local)
        #self.assertRaises(KeyError, conf._load)
        #print(conf)

    def test_env_missing1(self):
        os.environ["CORE4_OPTION_env1__k1__x1"] = "xxx"
        extra = tests.util.asset("config/extra2.py")
        local = tests.util.asset("config/local4.py")
        conf = MyConfig(extra_config=extra, config_file=local)
        conf._load()
        self.assertEqual(conf.env1.k1.x1, "xxx")

    def test_env_missing3(self):
        os.environ["CORE4_OPTION_env1__k1"] = "xxx"
        extra = tests.util.asset("config/extra2.py")
        local = tests.util.asset("config/local4.py")
        conf = MyConfig(extra_config=extra, config_file=local)
        conf._load()
        self.assertEqual(conf.env1.k1, "xxx")

    def test_env_missing2(self):
        os.environ["CORE4_OPTION_env1__k5"] = "xxx"
        extra = tests.util.asset("config/extra2.py")
        local = tests.util.asset("config/local4.py")
        conf = MyConfig(extra_config=extra, config_file=local)
        #self.assertRaises(KeyError, conf._load)
        conf._load()
        #print(conf)

    def test_cache(self):
        extra = tests.util.asset("config/extra2.py")
        local = tests.util.asset("config/local4.py")
        conf = core4.config.CoreConfig(extra_config=extra, config_file=local)
        k1 = list(conf.keys())
        self.assertTrue("mongo_url" in k1)
        self.assertTrue("env1" in k1)
        self.assertFalse("from cache" in conf.trace)

        conf2 = core4.config.CoreConfig(extra_config=extra, config_file=local)
        k2 = list(conf2.keys())
        #pprint(conf2)
        self.assertTrue("mongo_url" in k2)
        self.assertTrue("env1" in k2)

        self.assertTrue("from cache" in conf2.trace)

    def test_setter(self):
        extra = tests.util.asset("config/extra2.py")
        local = tests.util.asset("config/local4.py")
        conf = core4.config.CoreConfig(extra_config=extra, config_file=local)
        # print(conf)
        self.assertEqual(conf.account1.a, 1)
        conf.account1.a = 12
        self.assertEqual(conf.account1.a, 12)
        #print(conf.account1.a)
        #print(conf["account1"]["a"])
        self.assertEqual(conf["account1"]["a"], 12)
        conf["account1"]["a"] = 24
        #print(conf.account1.a)
        self.assertEqual(conf.account1.a, 24)
        #print(conf["account1"]["a"])
        self.assertEqual(conf["account1"]["a"], 24)

    def test_db(self):
        doc = {
            "_id": "1.global",
            "folder": {
                "root": "/tmp/core4test.tester"
            }
        }
        self.mongo.core4test.sys.conf.insert_one(doc)
        extra = tests.util.asset("config/extra2.py")
        local = tests.util.asset("config/local6.py")
        conf = MyConfig(extra_config=extra, config_file=local)
        conf._load()
        #print(conf.get_trace())
        self.assertEqual(conf.folder.root, "/tmp/core4test.tester")
        self.assertTrue("retrieved [1] configurations from "
                        "[core@localhost:27017/core4test/sys.conf]",
                        conf.trace)
        #print(conf.get_trace())

    def test_illegal_db(self):
        doc = {
            "_id": "1.global",
            "folder": {
                "root_X": "/tmp/core4test.tester"
            }
        }
        self.mongo.core4test.sys.conf.insert_one(doc)
        extra = tests.util.asset("config/extra2.py")
        local = tests.util.asset("config/local6.py")
        conf = MyConfig(extra_config=extra, config_file=local)
        #self.assertRaises(KeyError, conf.load)
        conf._load()
        #print(conf.get_trace())

    def test_multi_db(self):
        doc = {
            "_id": "1.global",
            "folder": {
                "root": "/tmp/core4test.tester2"
            }
        }
        self.mongo.core4test.sys.conf.insert_one(doc)
        doc = {
            "_id": "2.special",
            "folder": {
                "temp": "/tmp"
            }
        }
        self.mongo.core4test.sys.conf.insert_one(doc)
        extra = tests.util.asset("config/extra2.py")
        local = tests.util.asset("config/local6.py")
        conf = MyConfig(extra_config=extra, config_file=local)
        #print(conf.folder.root)
        #print(conf.folder.temp)
        self.assertEqual(conf.folder.root, "/tmp/core4test.tester2")
        self.assertEqual(conf.folder.temp, "/tmp")

    def test_cache2(self):
        doc = {
            "_id": "1.global",
            "folder": {
                "root": "/tmp/core4test.tester2"
            }
        }
        self.mongo.core4test.sys.conf.insert_one(doc)
        doc = {
            "_id": "2.special",
            "folder": {
                "temp": "/tmp"
            }
        }
        self.mongo.core4test.sys.conf.insert_one(doc)
        extra = tests.util.asset("config/extra2.py")
        local = tests.util.asset("config/local6.py")

        conf1 = core4.config.CoreConfig(extra_config=extra, config_file=local)
        conf1._load()
        self.assertFalse("from cache" in conf1.trace)
        #print(conf1.get_trace())

        conf2 = core4.config.CoreConfig(extra_config=extra, config_file=local)
        conf2._load()
        #self.assertFalse("from cache" in conf.get_trace())
        self.assertTrue("from cache" in conf2.trace)

    def test_env_first(self):

        class SystemConfig(MyConfig):
            user_config = tests.util.asset("config/user.py")
            system_config = tests.util.asset("config/system.py")

        os.environ["CORE4_CONFIG"] = tests.util.asset("config/env.py")
        conf = SystemConfig()
        conf._load()
        self.assertEqual(conf.folder.root, "/tmp/core4test.env")

    def test_user(self):

        class SystemConfig(MyConfig):
            user_config = tests.util.asset("config/user.py")
            system_config = tests.util.asset("config/system.py")

        conf = SystemConfig()
        conf._load()
        self.assertEqual(conf.folder.root, "/tmp/core4test.user")

    def test_system(self):

        class SystemConfig(MyConfig):
            user_config = tests.util.asset("config/_not_found_", exists=False)
            system_config = tests.util.asset("config/system.py")

        conf = SystemConfig()
        conf._load()
        self.assertEqual(conf.folder.root, "/tmp/core4test.system")

    def test_reserved(self):
        extra = tests.util.asset("config/extra3.py")
        local = tests.util.asset("config/local4.py")
        conf = core4.config.CoreConfig(extra_config=extra, config_file=local)
        self.assertRaises(core4.error.Core4ConfigurationError, conf._load)

    def test_not_found(self):
        class SystemConfig(MyConfig):
            user_config = tests.util.asset("config/user.py")
            system_config = tests.util.asset("config/system.py")

        os.environ["CORE4_CONFIG"] = tests.util.asset("_NOT_FOUND_",
                                                      exists=False)
        conf = SystemConfig()
        self.assertRaises(FileNotFoundError, conf._load)

    def test_reserved2(self):
        extra = tests.util.asset("config/extra4.py")
        local = tests.util.asset("config/local4.py")
        conf = core4.config.CoreConfig(extra_config=extra, config_file=local)
        self.assertRaises(core4.error.Core4ConfigurationError, conf._load)

    def test_file_mapping(self):
        extra = tests.util.asset("config/extra2.py")
        local = tests.util.asset("config/local7.py")
        conf = MyConfig(extra_config=extra, config_file=local)
        conf._load()
        self.assertEqual(conf.account1.deep.deeper.deepest.too_much, 987)

    def test_env_mapping(self):
        os.environ["CORE4_OPTION_account1__deep__deeper__deepest"] = "777"
        extra = tests.util.asset("config/extra2.py")
        local = tests.util.asset("config/local7.py")
        conf = core4.config.CoreConfig(extra_config=extra, config_file=local)
        conf._load()
        self.assertEqual(conf.account1.deep.deeper.deepest, "777")

    def test_env_mapping1(self):
        os.environ["CORE4_OPTION_account1"] = "777"
        extra = tests.util.asset("config/extra2.py")
        local = tests.util.asset("config/local7.py")
        conf = MyConfig(extra_config=extra, config_file=local)
        conf._load()
        self.assertEqual(conf.account1, "777")

    def test_env_mapping2(self):
        os.environ["CORE4_OPTION_account1__deep__deeper__deepest__another"] = "777"
        os.environ["CORE4_OPTION_account1__deep__deeper__hello__ciao"] = "123"
        extra = tests.util.asset("config/extra2.py")
        local = tests.util.asset("config/local7.py")
        conf = MyConfig(extra_config=extra, config_file=local)
        conf._load()
        #self.assertEqual(conf.account1, "777")
        #self.assertEqual(conf.account1.deep.deeper.deepest.too_much, 987)
        #self.assertEqual(conf.account1.deep.deeper.deepest.another, "777")
        #pprint(conf)

    def test_collection(self):
        extra = tests.util.asset("config/extra2.py")
        local = tests.util.asset("config/local6.py")
        conf = MyConfig(extra_config=extra, config_file=local)
        self.assertIn("username", repr(conf.sys.conf))
        self.assertIn("collection", repr(conf.sys.conf))
        self.assertIn("sys.conf", repr(conf.sys.conf))
        self.assertIn("core4test", repr(conf.sys.conf))
        self.assertNotIn("password", repr(conf.sys.conf))

if __name__ == '__main__':
    unittest.main()
