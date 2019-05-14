# -*- coding: utf-8 -*-

import os
import unittest

import datetime
import pymongo
import pymongo.errors

import core4.config
import core4.config.test
import core4.error
import tests.be.util


class MyConfig(core4.config.CoreConfig):
    cache = False


class TestConfig(unittest.TestCase):

    def setUp(self):
        dels = []
        for k in os.environ:
            if k.startswith('CORE4_'):
                dels.append(k)
        for k in dels:
            del os.environ[k]
        for db in ("", "1", "2"):
            self.mongo.drop_database('core4test' + db)

    def tearDown(self):
        tests.be.util.drop_env()

    @property
    def mongo(self):
        return pymongo.MongoClient('mongodb://core:654321@testmongo:27017')

    def test_yaml(self):
        conf = MyConfig()
        test = conf._read_yaml(conf.standard_config)
        self.assertEqual(test["DEFAULT"]["mongo_database"], "test")
        self.assertEqual(test["logging"]["stderr"], "INFO")

    def test_parse1(self):
        standard_config = {
            'DEFAULT': {
                'mongo_url': None,
                'mongo_database': 'test'
            },
            'sys': {
                'log': 'mongodb://sys.log',
                'role': 'mongodb://role.log'
            }
        }
        project_config = {
            'DEFAULT': {
                'mongo_database': 'mediaplus'
            },
            'tv': {
                'report_collection': 'mongodb://report',
                'agf_collection': 'mongodb://agf',
                'edi': {
                    'mongo_database': 'edidb',
                    'edi_collection': 'mongodb://data'
                }
            }
        }
        local_config = {
            'DEFAULT': {
                'mongo_url': 'mongodb://dev:27017'
            },
            'sys': {
                'mongo_database': 'core4'
            },
            'mediaplus': {
                'DEFAULT': {
                    'mongo_database': 'mediaplus_dev',
                    'mongo_url': 'mongodb://dev:27018'
                },
                'tv': {
                    'agf_collection': 'mongodb://prod:27017/mediaplus/agf'
                }
            }
        }
        conf = MyConfig()
        ret = conf._parse(standard_config, ("mediaplus", project_config),
                          local_config)
        self.assertEqual({
            'mediaplus': {
                'mongo_database': 'mediaplus_dev',
                'mongo_url': 'mongodb://dev:27018',
                'tv': {
                    'agf_collection': 'mongodb://prod:27017/mediaplus/agf',
                    'edi': {
                        'edi_collection': 'mongodb://data',
                        'mongo_database': 'edidb',
                        'mongo_url': 'mongodb://dev:27018'
                    },
                    'mongo_database': 'mediaplus_dev',
                    'mongo_url': 'mongodb://dev:27018',
                    'report_collection': 'mongodb://report'
                }
            },
            'mongo_database': 'test',
            'mongo_url': 'mongodb://dev:27017',
            'sys': {'log': 'mongodb://sys.log',
                    'mongo_database': 'core4',
                    'mongo_url': 'mongodb://dev:27017',
                    'role': 'mongodb://role.log'
                    }
        }, ret)

    def test_parse2(self):
        standard_config = {
            'DEFAULT': {
                'mongo_url': None,
                'mongo_database': 'test'
            },
            'sys': {
                'log': 'mongodb://sys.log',
                'role': 'mongodb://role.log'
            }
        }
        project_config = {
            'tv': {
                'agf_collection': 'mongodb://agf',
                'report_collection': 'mongodb://report',
                'edi': {
                    'mongo_database': 'edidb'
                }
            }
        }
        local_config = {
            'DEFAULT': {
                'mongo_url': 'mongodb://dev:27017'
            },
            'mediaplus': {
                'DEFAULT': {
                    'mongo_url': 'mongodb://host:27017'
                },
            }
        }
        conf = MyConfig()
        ret = conf._parse(standard_config, ("mediaplus", project_config),
                          local_config)
        self.assertEqual(
            {
                'mediaplus': {
                    'mongo_database': 'test',
                    'mongo_url': 'mongodb://host:27017',
                    'tv': {
                        'agf_collection': 'mongodb://agf',
                        'edi': {
                            'mongo_database': 'edidb',
                            'mongo_url': 'mongodb://host:27017'
                        },
                        'mongo_database': 'test',
                        'mongo_url': 'mongodb://host:27017',
                        'report_collection': 'mongodb://report'
                    }
                },
                'mongo_database': 'test',
                'mongo_url': 'mongodb://dev:27017',
                'sys': {
                    'log': 'mongodb://sys.log',
                    'mongo_database': 'test',
                    'mongo_url': 'mongodb://dev:27017',
                    'role': 'mongodb://role.log'
                }
            }, ret)

    def test_parse3(self):
        standard_config = {
            'DEFAULT': {
                'mongo_url': None,
                'mongo_database': 'test'
            },
            'sys': {
                'log': 'mongodb://sys.log',
                'role': 'mongodb://role.log'
            }
        }
        local_config = {
            'DEFAULT': {
                'mongo_url': 'mongodb://dev:27017',
                'mongo_database': 'core4test'
            },
            'sys': {
                'log': 'mongodb://sys-test.log'
            }
        }
        conf = MyConfig()
        ret = conf._parse(standard_config, None, local_config)
        self.assertEqual({
            'mongo_database': 'core4test',
            'mongo_url': 'mongodb://dev:27017',
            'sys': {
                'log': 'mongodb://sys-test.log',
                'mongo_database': 'core4test',
                'mongo_url': 'mongodb://dev:27017',
                'role': 'mongodb://role.log'
            }
        }, ret)

    def test_intersection1(self):
        standard_config = {
            'DEFAULT': {
                'mongo_url': None,
                'mongo_database': 'test'
            },
            'sys': {
                'log': 'mongodb://sys1.log'
            }
        }
        local_config = {
            'sys': {
                'log': 'mongodb://sys2.log',
                'unknown': 'mongodb://unknown'
            }
        }
        conf = MyConfig()
        ret = conf._parse(standard_config, None, local_config)
        # pprint(ret)
        self.assertNotIn("unknown", ret["sys"])

    def test_retype(self):
        standard_config = {
            'DEFAULT': {
                'int': 1,
                'float': 1.2,
                'bool': True,
                'list': [1, 2, 3],
                'dict': {"a": 5},
                'null': None
            },
            'section': {
                'log': 'mongodb://sys1.log'
            }
        }
        conf = MyConfig()

        def setter(k, v):
            c = conf._parse(standard_config, None, {'section': {k: v}})
            return c["section"][k]

        def raiser(*args):
            self.assertRaises(core4.error.Core4ConfigurationError,
                              setter, *args)

        self.assertEqual(2, setter("int", 2))
        self.assertIsNone(setter("int", None))
        self.assertEqual(2.1, setter("int", 2.1))
        raiser("int", True)
        raiser("int", "bla")

        self.assertEqual(2, setter("float", 2))
        self.assertIsNone(setter("float", None))
        self.assertEqual(2.1, setter("float", 2.1))
        raiser("float", [1, 2, 3])
        raiser("float", {})

        self.assertFalse(setter("bool", False))
        self.assertIsNone(setter("bool", None))
        raiser("bool", [1, 2, 3])
        raiser("bool", "")
        raiser("bool", -1)

        self.assertEqual(setter("list", [9, 8, 7]), [9, 8, 7])
        self.assertIsNone(setter("list", None))
        raiser("list", "")
        raiser("list", {})
        raiser("list", -1)

        self.assertEqual(setter("dict", {"a": 8}), {"a": 8})
        self.assertIsNone(setter("dict", None))
        raiser("dict", "")
        raiser("dict", [])
        raiser("dict", -1)

        self.assertEqual(setter("null", 1), 1)
        self.assertEqual(setter("null", "abc"), "abc")
        self.assertEqual(setter("null", True), True)
        self.assertEqual(setter("null", [1, 2, 3]), [1, 2, 3])

    def test_syntax(self):
        extra = tests.be.util.asset("config/empty.yaml")
        local = tests.be.util.asset("config/local4.yaml")
        conf = MyConfig(project_config=("test", extra), config_file=local)
        self.assertRaises(core4.error.Core4ConfigurationError,
                          conf._load)

    def test_default_type(self):
        standard_config = {
            'section': {
                'test': True
            }
        }
        conf = MyConfig()
        self.assertRaises(core4.error.Core4ConfigurationError,
                          conf._parse, standard_config,
                          ('test', {'DEFAULT': 1, 'abc': True}))
        standard_config = {
            'DEFAULT': [],
            'section': {
                'test': True
            }
        }
        conf = MyConfig()
        self.assertRaises(core4.error.Core4ConfigurationError,
                          conf._parse, standard_config,
                          ('test', {'abc': True}))
        standard_config = {
            'section': {
                'test': True
            }
        }
        conf = MyConfig()
        conf._parse(standard_config, ('test', {'abc': True}),
                    {"section": {"test": False}})
        self.assertRaises(core4.error.Core4ConfigurationError,
                          conf._parse, standard_config,
                          ('test', {'abc': True}),
                          {"section": {"test": False}, "DEFAULT": ""})

    def test_connect(self):
        extra = tests.be.util.asset("config/empty.yaml")
        local = tests.be.util.asset("config/local1.yaml")
        conf = MyConfig(project_config=("test", extra), config_file=local)
        conf._load()
        self.assertEqual(conf["sys"]["log"].info_url,
                         "core@testmongo:27017/core4test1/sys.log")
        self.assertEqual(conf["sys"]["log"].count_documents({}), 0)
        coll = conf["sys"]["log"]
        coll.insert_one({})
        self.assertEqual(conf["sys"]["log"].count_documents({}), 1)
        self.assertEqual(1, self.mongo.core4test1.sys.log.count_documents({}))

    def test_connect2(self):
        extra = tests.be.util.asset("config/extra1.yaml")
        local = tests.be.util.asset("config/local6.yaml")
        conf = MyConfig(project_config=("test", extra), config_file=local)
        conf._load()
        self.assertEqual(conf["sys"]["log"].info_url,
                         "core@testmongo:27017/core4test/sys.log")
        self.assertRaises(pymongo.errors.OperationFailure,
                          conf["sys"]["log"].count_documents, {})

        self.assertEqual(conf.test.coll1.info_url,
                         "core@testmongo:27017/core4test2/coll1")
        self.assertEqual(0, conf.test.coll1.count_documents({}))
        conf.test.coll1.insert_one({})
        self.assertEqual(1, conf.test.coll1.count_documents({}))
        self.assertEqual(1, self.mongo.core4test2.coll1.count_documents({}))
        self.assertEqual(conf.test.coll2.info_url,
                         "core@testmongo:27017/core4test/coll2")
        conf.test.coll2.insert_one({})
        self.assertEqual(1, conf.test.coll2.count_documents({}))
        self.assertEqual(1, self.mongo.core4test.coll2.count_documents({}))
        self.assertEqual(0, self.mongo.core4test1.coll2.count_documents({}))
        self.assertEqual(0, self.mongo.core4test2.coll2.count_documents({}))
        self.assertEqual(
            "!connect "
            "'mongodb://core:654321@testmongo:27017/core4test/coll2/collx'",
            str(conf.test.coll3))
        self.assertRaises(core4.error.Core4ConfigurationError,
                          conf.test.coll3.connect)

    def test_env_file(self):
        extra = tests.be.util.asset("config/empty.yaml")
        os.environ["CORE4_CONFIG"] = tests.be.util.asset("config/local1.yaml")
        conf = MyConfig(project_config=("test", extra))
        self.assertEqual(conf["sys"]["log"].info_url,
                         "core@testmongo:27017/core4test1/sys.log")
        self.assertEqual(conf["sys"]["log"].count_documents({}), 0)
        coll = conf["sys"]["log"]
        coll.insert_one({})
        self.assertEqual(conf["sys"]["log"].count_documents({}), 1)
        self.assertEqual(1, self.mongo.core4test1.sys.log.count_documents({}))

    def test_not_found(self):
        extra = tests.be.util.asset("config/nf", exists=False)
        os.environ["CORE4_CONFIG"] = tests.be.util.asset("config/local1.yaml")
        conf = MyConfig(project_config=("test", extra))
        self.assertEqual(str(conf.sys.log), "!connect 'mongodb://sys.log'")

        extra = tests.be.util.asset("config/empty.yaml")
        os.environ["CORE4_CONFIG"] = tests.be.util.asset("config/nf",
                                                         exists=False)
        conf = MyConfig(project_config=("test", extra))
        self.assertRaises(FileNotFoundError, conf._load)

    def test_user_file(self):
        extra = tests.be.util.asset("config/extra1.yaml")
        user_file = tests.be.util.asset("config/user.yaml")
        system_file = tests.be.util.asset("config/system.yaml")

        class Config(MyConfig):
            user_config = user_file
            system_config = system_file

        conf = Config(project_config=("test", extra))
        self.assertEqual(conf["sys"]["log"].info_url,
                         "core@testmongo:27017/core4test1/sys.log")
        self.assertEqual(conf["sys"]["log"].count_documents({}), 0)
        coll = conf["sys"]["log"]
        coll.insert_one({})
        self.assertEqual(conf["sys"]["log"].count_documents({}), 1)
        self.assertEqual(1, self.mongo.core4test1.sys.log.count_documents({}))
        self.assertEqual(conf.test.value, 2)

    def test_system_file(self):
        extra = tests.be.util.asset("config/extra1.yaml")
        user_file = tests.be.util.asset("config/nf", exists=False)
        system_file = tests.be.util.asset("config/system.yaml")

        class Config(MyConfig):
            user_config = user_file
            system_config = system_file

        conf = Config(project_config=("test", extra))
        self.assertEqual(conf["sys"]["log"].info_url,
                         "core@testmongo:27017/core4test2/sys.log")
        self.assertEqual(conf["sys"]["log"].count_documents({}), 0)
        coll = conf["sys"]["log"]
        coll.insert_one({})
        self.assertEqual(conf["sys"]["log"].count_documents({}), 1)
        self.assertEqual(1, self.mongo.core4test2.sys.log.count_documents({}))
        self.assertEqual(conf.test.value, 4)

    def test_no_default_connect(self):
        extra = tests.be.util.asset("config/empty.yaml")
        local = tests.be.util.asset("config/local2.yaml")
        conf = MyConfig(project_config=("test", extra), config_file=local)
        conf._load()
        self.assertEqual(conf["sys"]["log"].info_url,
                         "core@testmongo:27017/core4test/sys.log")
        self.assertEqual(conf["sys"]["log"].count_documents({}), 0)
        coll = conf["sys"]["log"]
        coll.insert_one({})
        self.assertEqual(conf["sys"]["log"].count_documents({}), 1)

    def test_empty_connect(self):
        extra = tests.be.util.asset("config/empty.yaml")
        local = tests.be.util.asset("config/empty.yaml")
        conf = MyConfig(project_config=("test", extra), config_file=local)
        conf._load()
        with self.assertRaises(core4.error.Core4ConfigurationError):
            conf.sys.log.connect()

    def test_readonly(self):
        extra = tests.be.util.asset("config/empty.yaml")
        local = tests.be.util.asset("config/empty.yaml")
        conf = MyConfig(project_config=("test", extra), config_file=local)
        self.assertEqual(conf.mongo_database, "test")

        def set1():
            conf["mongo_url"] = "xyz"

        self.assertRaises(core4.error.Core4ConfigurationError, set1)

        def del1():
            del conf["mongo_url"]

        self.assertRaises(core4.error.Core4ConfigurationError, del1)

        def set2():
            conf.logging.stderr = "ERROR"

        self.assertRaises(core4.error.Core4ConfigurationError, set2)

        def set3():
            conf["logging"]["stderr"] = "CRITICAL"

        self.assertRaises(core4.error.Core4ConfigurationError, set3)
        self.assertRaises(core4.error.Core4ConfigurationError, conf.pop,
                          "logging")
        self.assertRaises(core4.error.Core4ConfigurationError, conf.popitem)
        self.assertRaises(core4.error.Core4ConfigurationError, conf.clear)
        self.assertRaises(core4.error.Core4ConfigurationError, conf.update,
                          {"a": 1})
        self.assertRaises(core4.error.Core4ConfigurationError, conf.setdefault,
                          "a", "abc")

    def test_iter(self):
        extra = tests.be.util.asset("config/empty.yaml")
        local = tests.be.util.asset("config/empty.yaml")
        conf = MyConfig(project_config=("test", extra), config_file=local)
        self.assertIn("mongo_database", conf.keys())
        self.assertIn("sys", conf.keys())
        self.assertIn("logging", conf.keys())
        self.assertIn("mongo_url", conf.keys())
        self.assertIn("folder", conf.keys())
        t1 = list(conf.items())
        t2 = list(iter(conf))
        self.assertIn(("mongo_database", "test"), t1)
        self.assertIn(("mongo_database", "test"), t2)

    def test_values(self):
        extra = tests.be.util.asset("config/empty.yaml")
        local = tests.be.util.asset("config/empty.yaml")
        conf = MyConfig(project_config=("test", extra), config_file=local)
        v = conf.values()
        self.assertEqual(v._mapping.mongo_database, "test")
        self.assertEqual(len(v), len(conf))

    def test_dot(self):
        extra = tests.be.util.asset("config/empty.yaml")
        local = tests.be.util.asset("config/local1.yaml")
        conf = MyConfig(project_config=("test", extra), config_file=local)
        conf._load()
        conf.sys.log.insert_one({})
        self.assertEqual(1, conf.sys.log.count_documents({}))

    def test_extra_no_project(self):
        extra = tests.be.util.asset("config/extra1.yaml")
        os.environ["CORE4_CONFIG"] = tests.be.util.asset("config/empty.yaml")
        conf = MyConfig(project_config=("test", extra))
        self.assertEqual(conf.folder.archive, "arch")

    def test_reserved_word(self):
        standard_config = {
            '_DEFAULT': {
                'c': "mongodb://core4test:27017"
            },
        }
        conf = MyConfig()
        self.assertRaises(core4.error.Core4ConfigurationError,
                          conf._parse, standard_config, None, None)

    def test_read_db(self):
        self.mongo.core4test.sys.conf.insert_one({
            "folder": {
                "transfer": "/tmp"
            },
            "logging": {
                "exception": {
                    "capacity": 1,
                    "irrelevant": 42
                },
                "stderr": "WARNING"
            }
        })
        local = tests.be.util.asset("config/local3.yaml")
        conf = MyConfig(project_config=None, config_file=local)
        conf._load()
        self.assertEqual(conf.folder.transfer, "/tmp")
        self.assertEqual(conf.logging.exception.capacity, 1)
        self.assertEqual(conf.logging.stderr, "WARNING")
        self.assertNotIn("irrelevant", conf.logging.exception)

        self.mongo.core4test.sys.conf.insert_one({
            "logging": {
                "exception": {
                    "capacity": 42,
                },
                "stderr": "INFO"
            }
        })
        conf = MyConfig(project_config=None, config_file=local)
        conf._load()
        self.assertEqual(conf.folder.transfer, "/tmp")
        self.assertEqual(conf.logging.exception.capacity, 42)
        self.assertEqual(conf.logging.stderr, "INFO")
        self.assertNotIn("irrelevant", conf.logging.exception)
        assert conf.db_info == "core@testmongo:27017/core4test/sys.conf"

    def test_read_no_db(self):
        local = tests.be.util.asset("config/local3.yaml")
        conf = MyConfig(project_config=None, config_file=local)
        conf._load()
        self.assertEqual(conf.folder.transfer, "transfer")
        self.assertEqual(conf.logging.exception.capacity, 99)
        self.assertEqual(conf.logging.stderr, "INFO")
        self.assertNotIn("irrelevant", conf.logging.exception)
        assert conf.db_info == "core@testmongo:27017/core4test/sys.conf"

    def test_extra_read_db(self):
        self.mongo.core4test.sys.conf.insert_one({
            "folder": {
                "transfer": "/tmp"
            },
            "logging": {
                "exception": {
                    "capacity": 1,
                    "irrelevant": 42
                },
                "stderr": "WARNING"
            },
            "test": {
                "value": 66
            }
        })
        local = tests.be.util.asset("config/local3.yaml")
        extra = tests.be.util.asset("config/extra1.yaml")
        conf = MyConfig(project_config=("test", extra), config_file=local)
        conf._load()
        self.assertEqual(conf.folder.transfer, "/tmp")
        self.assertEqual(conf.logging.exception.capacity, 1)
        self.assertEqual(conf.logging.stderr, "WARNING")
        self.assertNotIn("irrelevant", conf.logging.exception)
        self.assertEqual(conf.test.value, 66)

    def test_repr(self):
        extra = tests.be.util.asset("config/extra1.yaml")
        os.environ["CORE4_CONFIG"] = tests.be.util.asset("config/empty.yaml")
        conf = MyConfig(project_config=("test", extra))
        _ = str(conf)

    def test_env(self):
        os.environ[
            "CORE4_OPTION_DEFAULT__mongo_url"] = \
            "mongodb://core:654321@testmongo:27017"
        os.environ[
            "CORE4_OPTION_sys__mongo_database"] = "core4test2"
        local = tests.be.util.asset("config/empty.yaml")
        conf = MyConfig(config_file=local)
        self.assertEqual("test", conf.mongo_database)
        self.assertEqual('mongodb://core:654321@testmongo:27017',
                         conf.mongo_url)
        self.assertEqual("test", conf.logging.mongo_database)
        self.assertEqual('mongodb://core:654321@testmongo:27017',
                         conf.logging.mongo_url)
        self.assertEqual("core4test2", conf.sys.mongo_database)
        self.assertEqual('mongodb://core:654321@testmongo:27017',
                         conf.sys.mongo_url)

    def test_env_connect(self):
        os.environ[
            "CORE4_OPTION_DEFAULT__mongo_url"] = \
            "mongodb://core:654321@testmongo:27017"
        os.environ[
            "CORE4_OPTION_DEFAULT__mongo_database"] = "core4test"
        os.environ[
            "CORE4_OPTION_sys__log"] = "!connect mongodb://coll1"
        empty = tests.be.util.asset("config/empty.yaml")
        conf = MyConfig(config_file=empty)
        self.assertEqual(0, conf.sys.log.count_documents({}))
        for i in range(10):
            conf.sys.log.insert_one({})
        self.assertEqual(10, self.mongo.core4test.coll1.count_documents({}))

    def test_env_db(self):
        os.environ[
            "CORE4_OPTION_sys__conf"] = "!connect mongodb://core:654321@testmongo:27017/core4test2/sysconf"
        self.mongo.core4test2.sysconf.insert_one({
            "sys": {
                "log": "!connect mongodb://core:654321@testmongo:27017/"
                       "core4test1/coll1"
            }
        })
        empty = tests.be.util.asset("config/empty.yaml")
        conf = MyConfig(config_file=empty)
        conf._load()
        self.assertEqual(0, conf.sys.log.count_documents({}))
        for i in range(5):
            self.mongo.core4test1.coll1.insert_one({})
        self.assertEqual(5, conf.sys.log.count_documents({}))

    def test_env_db2(self):
        os.environ[
            "CORE4_OPTION_sys__mongo_url"] = "mongodb://core:654321@testmongo:27017"
        os.environ[
            "CORE4_OPTION_sys__mongo_database"] = "core4test"
        os.environ[
            "CORE4_OPTION_sys__conf"] = "!connect mongodb://sys.conf"
        self.mongo.core4test.sys.conf.insert_one({
            "sys": {
                "log": "!connect mongodb://core:654321@testmongo:27017/"
                       "core4test1/coll1"
            }
        })
        empty = tests.be.util.asset("config/empty.yaml")
        conf = MyConfig(config_file=empty)
        # conf._load()
        self.assertEqual(conf["sys"]["conf"].info_url,
                         "core@testmongo:27017/core4test/sys.conf")
        self.assertEqual(conf["sys"]["log"].info_url,
                         "core@testmongo:27017/core4test1/coll1")

        # self.assertEqual(0, conf.sys.log.count_documents({}))
        # for i in range(5):
        #     self.mongo.core4test1.coll1.insert_one({})
        # self.assertEqual(5, conf.sys.log.count_documents({}))

    def test_db_connect(self):
        os.environ[
            "CORE4_OPTION_DEFAULT__mongo_url"] = \
            "mongodb://core:654321@testmongo:27017"
        os.environ[
            "CORE4_OPTION_sys__mongo_database"] = "core4test"
        self.mongo.core4test.sys.conf.insert_one({
            "sys": {
                "log": "!connect mongodb://core4test1/coll1"
            }
        })
        local = tests.be.util.asset("config/local3.yaml")
        conf = MyConfig(config_file=local)
        self.assertEqual(0, conf.sys.log.count_documents({}))
        for i in range(5):
            self.mongo.core4test1.coll1.insert_one({})
        self.assertEqual(5, conf.sys.log.count_documents({}))

    def test_db_connect1(self):
        os.environ[
            "CORE4_OPTION_sys__mongo_url"] = \
            "mongodb://core:654321@testmongo:27017"
        os.environ[
            "CORE4_OPTION_sys__mongo_database"] = "core4test"
        self.mongo.core4test.sys.conf.insert_one({
            "sys": {
                "log": "!connect mongodb://core4test1/coll1"
            }
        })
        local = tests.be.util.asset("config/local3.yaml")
        conf = MyConfig(config_file=local)
        self.assertEqual(0, conf.sys.log.count_documents({}))
        for i in range(5):
            self.mongo.core4test1.coll1.insert_one({})
        self.assertEqual(5, conf.sys.log.count_documents({}))

    def test_db_connect2(self):
        self.mongo.core4test.sys.conf.insert_one({
            "sys": {
                "log": "!connect mongodb://core:654321@testmongo:27017/"
                       "core4test1/coll1"
            }
        })
        local = tests.be.util.asset("config/local5.yaml")
        conf = MyConfig(config_file=local)
        self.assertEqual(0, conf.sys.log.count_documents({}))
        for i in range(5):
            self.mongo.core4test1.coll1.insert_one({})
        self.assertEqual(5, conf.sys.log.count_documents({}))

    def test_tag(self):
        extra = tests.be.util.asset("config/extra1.yaml")
        empty = tests.be.util.asset("config/empty.yaml")
        conf = MyConfig(project_config=("test", extra), config_file=empty)
        self.assertEqual(conf.test.v1, 3)
        self.assertIsInstance(conf.test.v1, float)
        self.assertTrue(conf.test.v2)
        self.assertIsInstance(conf.test.v2, bool)

    def test_env_tag(self):
        extra = tests.be.util.asset("config/extra1.yaml")
        empty = tests.be.util.asset("config/empty.yaml")
        os.environ["CORE4_OPTION_test__coll1"] = "~"
        os.environ["CORE4_OPTION_test__v1"] = "!!float 33.5"
        os.environ["CORE4_OPTION_test__v2"] = "!!bool off"
        os.environ["CORE4_OPTION_test__v3"] = "!!int 10"
        os.environ["CORE4_OPTION_test__v4"] = "!!str 456"
        os.environ["CORE4_OPTION_test__v5"] = "!!timestamp 2014-04-14"
        os.environ["CORE4_OPTION_test__v6"] = "!!timestamp 2014-04-14 12:23"
        conf = MyConfig(project_config=("test", extra), config_file=empty)
        conf._load()
        self.assertIsInstance(conf.test.v5, datetime.datetime)
        self.assertIsInstance(conf.test.v6, datetime.date)
        self.assertIsNone(conf["test"]["coll1"])
        self.assertEqual(conf["test"]["v1"], 33.5)
        self.assertEqual(conf["test"]["v4"], "456")
        self.assertFalse(conf["test"]["v2"])

    def test_tag_timestamp(self):
        extra = tests.be.util.asset("config/extra1.yaml")
        empty = tests.be.util.asset("config/empty.yaml")
        conf = MyConfig(project_config=("test", extra), config_file=empty)
        conf._load()
        self.assertIsInstance(conf.test.v5, datetime.datetime)
        self.assertIsInstance(conf.test.v6, datetime.date)

    def test_env_tag_invalid(self):
        extra = tests.be.util.asset("config/extra1.yaml")
        empty = tests.be.util.asset("config/empty.yaml")
        os.environ["CORE4_OPTION_test__v2"] = "!!bool 123"
        conf = MyConfig(project_config=("test", extra), config_file=empty)
        self.assertRaises(core4.error.Core4ConfigurationError, conf._load)

    def test_dev_default(self):
        extra = tests.be.util.asset("config/extra1.yaml")
        empty = tests.be.util.asset("config/empty.yaml")
        conf = MyConfig(project_config=("test", extra), config_file=empty)
        print(conf.test.v7)
        print(conf.test.get("v8", "abc"))
        print(conf.test.v9)

    def test_test_config(self):
        config = core4.config.test.TestConfig(project_name="test1",
                                              extra_dict={"test1": {"abc": 1}},
                                              local_dict={"test1": {"abc": 2}})
        self.assertEqual(config.test1.abc, 2)
        config = core4.config.test.TestConfig(project_name="test1",
                                              extra_dict={"test1": {"abc": 1}})
        self.assertEqual(config.test1.abc, 1)

    def test_project_default(self):
        extra = tests.be.util.asset("config/extra2.yaml")
        local = tests.be.util.asset("config/local8.yaml")
        conf = MyConfig(project_config=("test", extra), config_file=local)
        #self.assertEqual(conf.sys.mongo_url, "mongodb://testmongo:27017")
        self.assertEqual(conf.test.job.mongo_url, "mongodb://testhost")
        self.assertEqual(conf.test.job.schedule, "30 * * * *")
        self.assertEqual(conf.test.job.test.my_job.schedule, "10 * * * *")
        self.assertFalse("nf1" in conf.test.job.test.my_job)
        self.assertTrue("nf2" in conf.test.job)
        self.assertEqual("xyz", conf.test.job.nf2)
        self.assertEqual("b", conf.test.nf2)
        self.assertTrue("value" in conf.test.job)
        self.assertTrue("value" in conf.test.job.test.my_job)
        self.assertEqual(345, conf.test.job.value)
        self.assertEqual(999, conf.test.job.test.my_job.value)

    def test_extra_config(self):
        config = core4.config.test.TestConfig(
            project_name="test1",
            project_dict={
                "abc": 1,
                "def": 99,
                "DEFAULT": {
                    "default_value": 123
                }
            },
            local_dict={
                "test1": {
                    "abc": 2,
                    "extra_value": 987,
                    "not_exists": "bla"
                }
            },
            extra_dict={
                "test1": {
                    "extra_value": None,
                    "deep_dict": {}
                }
            }
        )
        self.assertEqual(config.test1.extra_value, 987)
        self.assertEqual(config.test1.abc, 2)
        self.assertEqual(config.test1["def"], 99)
        self.assertEqual(config.test1.default_value, 123)
        self.assertEqual(config.test1.deep_dict.default_value, 123)
        self.assertEqual(config.test1.deep_dict.mongo_database, "test")

    def test_db_default(self):
        self.mongo.core4test.sys.conf.insert_one({
            "folder": {
                "root": "/tmp"
            },
            "DEFAULT": {
                "mongo_url": "mongodb://core:654321@testmongo:27017",
                "mongo_database": "abc"
            }
        })
        local = tests.be.util.asset("config/local5.yaml")
        conf = MyConfig(config_file=local)
        self.assertEqual(
            str(conf.sys.conf),
            "!connect 'mongodb://core:654321@testmongo:27017"
            "/core4test/sys.conf'")
        self.assertEqual(
            conf.sys.role.info_url, "core@testmongo:27017/abc/sys.role")

    def test_mongo_url_no_str(self):
        self.mongo.core4test.sys.conf.insert_one({
            "folder": {
                "root": "/tmp"
            },
            "DEFAULT": {
                "mongo_url": "!connect mongodb://core:654321@testmongo:27017",
                "mongo_database": "abc"
            }
        })
        local = tests.be.util.asset("config/local5.yaml")
        conf = MyConfig(config_file=local)
        self.assertEqual(
            str(conf.sys.conf),
            "!connect 'mongodb://core:654321@testmongo:27017"
            "/core4test/sys.conf'")
        with self.assertRaises(core4.error.Core4ConfigurationError):
            x = conf.sys.role.info_url()

    def test_error_config(self):
        local = tests.be.util.asset("config/error.yaml")
        conf = MyConfig(config_file=local)
        with self.assertRaises(core4.error.Core4ConfigurationError):
            _ = conf.config

    def test_folder(self):
        local = tests.be.util.asset("config/empty.yaml")
        config = MyConfig(config_file=local)
        assert config.get_folder("temp") == "/tmp/core4/temp"
        assert config.get_folder("home") is None


if __name__ == '__main__':
    unittest.main(exit=False)
