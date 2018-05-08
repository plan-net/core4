# -*- coding: utf-8 -*-

import configparser
import os
import unittest

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
        self.assertEqual('mongodb://localhost:27018', config.get('mongo_url'))
        self.assertEqual('test_database', config.get('mongo_database'))
        self.assertEqual(config.sections(),
                         ['bitbucket.org', 'topsecret.server.com'])
        self.assertTrue(config.has_option('mongo_url'))
        self.assertFalse(config.has_option('bla_bla'))
        self.assertTrue(config.has_option('test_default'))
        self.assertTrue(config.getboolean('test_default'))

    def test_default(self):
        # no user config
        # no system config
        # only default
        config = TestConfig()
        self.assertEqual('core4dev', config.get('mongo_database'))

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
        print(config.get_datetime("test_date1"))


if __name__ == '__main__':
    unittest.main()
