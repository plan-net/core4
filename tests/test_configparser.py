# -*- coding: utf-8 -*-

import configparser
import datetime
import os
import re
import unittest

import pymongo

import core4.config
import tests.util


class TestConfig(core4.config.CoreConfig):
    user_config = tests.util.asset('__NO_FILE__', exists=False)
    system_config = tests.util.asset('__NO_FILE__', exists=False)


class TestSystemConfig(TestConfig):
    system_config = tests.util.asset('configparser/system.conf')


class TestUserConfig(TestSystemConfig):
    user_config = tests.util.asset('configparser/user.conf')


class TestConfigParser(unittest.TestCase):

    def setUp(self):
        dels = []
        for k in os.environ:
            if k.startswith('CORE4_'):
                dels.append(k)
        for k in dels:
            del os.environ[k]
        for cls in [core4.config.main.CoreConfig, TestConfig,
                    TestSystemConfig, TestUserConfig]:
            cls.purge_cache()
        self.mongo.drop_database('core4test')
        self.mongo.drop_database('core4test1')

    @property
    def mongo(self):
        return pymongo.MongoClient('mongodb://core:654321@localhost:27017')

    def test_orig(self):
        # test plain configparser and test-internal asset method
        config = configparser.ConfigParser()
        inifile1 = tests.util.asset('configparser/simple.conf')
        config.read(inifile1)
        self.assertEqual(sorted(['bitbucket.org', 'topsecret.server.com']),
                         sorted(config.sections()))
        inifile2 = tests.util.asset('configparser', 'simple.conf')
        config.read(inifile2)
        self.assertEqual(inifile1, inifile2)
        self.assertRaises(FileNotFoundError, tests.util.asset,
                          'configparser', 'simple.conf', 'bla')

    def test_load(self):
        config = TestConfig(config_file=tests.util.asset(
            'configparser/simple.conf'))
        self.assertEqual(len(config.path), 2)
        self.assertEqual(os.path.basename(config.path[0]), 'core.conf')
        self.assertEqual(os.path.basename(config.path[1]), 'simple.conf')
        self.assertEqual('mongodb://core:654321@localhost:27017',
                         config.get('mongo_url'))
        self.assertEqual('test_database', config.get('mongo_database'))
        self.assertEqual(config.sections(), ['kernel', 'bitbucket.org',
                                             'topsecret.server.com'])
        self.assertTrue(config.has_option('mongo_url'))
        self.assertFalse(config.has_option('bla_bla'))
        self.assertTrue(config.has_option('test_default'))
        self.assertTrue(config.getboolean('test_default'))

    def test_default(self):
        # no user config
        # no system config
        # only default
        config = TestConfig()
        value = config.get('mongo_database')
        self.assertEqual('core4dev', value)

    def test_system(self):
        # no user config
        # fixed system config
        config = TestSystemConfig()
        self.assertEqual('mongo in system', config.get('mongo_database'))

    def test_system_env(self):
        # no user config
        # fixed system config
        # but: CORE4_CONFIG wins
        os.environ['CORE4_CONFIG'] = tests.util.asset(
            'configparser/simple.conf')
        config = TestSystemConfig()
        self.assertEqual('test_database', config.get('mongo_database'))

    def test_user(self):
        # fixed user config
        # fixed system config
        config = TestUserConfig()
        self.assertEqual('mongo in user', config.get('mongo_database'))

    def test_user_env(self):
        # fixed user config
        # fixed system config
        # but: CORE4_CONFIG wins
        os.environ['CORE4_CONFIG'] = tests.util.asset(
            'configparser/simple.conf')
        config = TestUserConfig()
        self.assertEqual('test_database', config.get('mongo_database'))

    def test_blending(self):
        # fixed system config
        config = TestSystemConfig()
        self.assertEqual('mongo in system', config.get('mongo_database'))
        self.assertEqual('mb', config.get('User', section='bitbucket.org'))
        self.assertFalse(config.has_option('User1'))
        # fixed system config and extra config
        config = TestSystemConfig(
            extra_config=tests.util.asset('configparser/simple.conf'))
        self.assertEqual('mongo in system', config.get('mongo_database'))
        self.assertEqual('mb', config.get('User', section='bitbucket.org'))
        self.assertEqual('mr', config.get('User1', section='bitbucket.org'))

    def test_undefn(self):
        # fixed system config and extra config
        config = TestSystemConfig(
            extra_config=tests.util.asset('configparser/simple.conf'))
        self.assertEqual('mongo in system', config.get('mongo_database'))
        self.assertEqual('mb', config.get('User', section='bitbucket.org'))
        self.assertEqual('mr', config.get('User1', section='bitbucket.org'))
        self.assertEqual(config.get('mongo_url'), "")

    def test_getter(self):
        config = TestUserConfig('format')
        self.assertEqual("2018-01-28", config.get('test_date1'))
        v = config.get_datetime("test_date1")
        self.assertEqual(datetime.datetime(2018, 1, 28), v)
        self.assertRaises(ValueError, config.get_datetime, "test_date2")
        v = config.get_datetime("test_date3")
        self.assertEqual(datetime.datetime(2018, 1, 28, 3, 59), v)
        v = config.get_datetime("test_date4")
        self.assertEqual(datetime.datetime(2018, 5, 8, 13, 50, 33), v)
        v = config.get_datetime("test_date5")
        self.assertEqual(datetime.datetime(2018, 1, 28), v)
        v = config.get_datetime("test_date6")
        self.assertEqual(datetime.datetime(2018, 1, 28, 11, 12, 13), v)
        v = config.get_datetime("test_date7")
        self.assertEqual(datetime.datetime(2018, 1, 28, 3, 59), v)
        v = config.get_datetime("test_date8")
        self.assertEqual(datetime.datetime(2018, 1, 28, 3, 59), v)
        v = config.get_datetime("test_time1")
        v = datetime.time(v.hour, v.minute, v.second, v.microsecond)
        self.assertEqual(datetime.time(3, 59), v)

    def test_regex(self):
        config = TestUserConfig('format')

        v = config.get_regex("test_regex1")
        t = v.search('business intelligence')
        self.assertEqual('.*intelli.*', t.re.pattern)
        self.assertIsNotNone(t)

        t = v.search('Business Intelligence')
        self.assertIsNone(t)

        v = config.get_regex("test_regex2")
        t = v.search('Business Intelligence')
        self.assertEqual('.*intelli.*', t.re.pattern)
        self.assertIsNotNone(t)

        self.assertRaises(re.error, config.get_regex, "test_regex3")

    def test_connection(self):
        config = TestUserConfig('format')
        v = config.get_collection('test_conn1')
        self.assertEqual(
            str(v),
            "CoreConnection(scheme='mongodb', hostname='localhost:27017', "
            "username='None', database='db', collection='c.d.e')",
        )

        v = config.get_collection('test_conn2')
        self.assertEqual(
            str(v),
            "CoreConnection(scheme='mongodb', hostname='localhost:27017', "
            "username='admin', database='db2', collection='coll')",
        )

        self.assertRaises(ValueError, config.get_collection, 'test_conn3')

        v = config.get_collection('test_conn4')
        self.assertEqual(
            str(v),
            "CoreConnection(scheme='mongodb', hostname='localhost:27017', "
            "username='core3', database='db1', collection='c1')",
        )

        v = config.get_collection('test_conn5')
        self.assertEqual(
            str(v),
            "CoreConnection(scheme='mongodb', hostname='localhost:27017', "
            "username='admin', database='db3', collection='c1')",
        )

        v = config.get_collection('test_conn6')
        self.assertEqual(
            str(v),
            "CoreConnection(scheme='mongodb', hostname='localhost:27017', "
            "username='core3', database='db2', collection='c3')",
        )
        self.assertEqual(v.info_url, "core3@localhost:27017/db2/c3")

    def test_access(self):
        config = TestUserConfig('connect')
        coll = config.get_collection('test_conn1')
        self.assertEqual(0, coll.count())
        for i in range(1, 100):
            coll.insert_one({'no': i})
        self.assertEqual(99, coll.count())
        self.assertEqual("CoreConnection("
                         "scheme='mongodb', "
                         "hostname='localhost:27017', "
                         "username='core', "
                         "database='core4test', "
                         "collection='collection')",
                         str(coll))

    def test_db_conf(self):
        config = TestConfig('test1', config_file=tests.util.asset(
            'configparser/db.conf'))
        self.assertTrue("coll1" in config.options("test1"))
        self.assertTrue(config.has_section("test1"))
        self.assertFalse(config.has_section("test2"))
        # make some db config
        db_conf = config.get_collection('sys.conf', 'kernel')
        db_conf.insert_one({
            '_id': 'test2',
            'option': {
                'coll1': 'test2coll1'
            }
        })
        db_conf.insert_one({
            '_id': 'test1',
            'option': {
                'coll1': 'test1coll1'
            }
        })
        config = TestConfig('test1', config_file=tests.util.asset(
            'configparser/db.conf'))
        self.assertTrue("coll1" in config.options("test1"))
        self.assertTrue(config.has_section("test1"))
        self.assertFalse(config.has_section("test2"))

        TestConfig.purge_cache()
        config = TestConfig('test1', config_file=tests.util.asset(
            'configparser/db.conf'))
        self.assertTrue("coll1" in config.options("test1"))
        self.assertTrue(config.has_section("test1"))
        self.assertTrue(config.has_section("test2"))
        self.assertEqual("test1coll1", config.get("coll1"))
        self.assertEqual("test2coll1", config.get("coll1", "test2"))

    # def test_fail(self):
    #     self.assertTrue(False)


if __name__ == '__main__':
    unittest.main()
