import os
import unittest
import pymongo
import core4.base.cookie
import core4.config
import tests.util


class MyConfig(core4.config.CoreConfig):
    _cache = None


class TestCookie(unittest.TestCase):
    @property
    def mongo(self):
        return pymongo.MongoClient('mongodb://core:654321@localhost:27017')

    def testSet(self):
        os.environ["CORE4_CONFIG"] = tests.util.asset("config/local7.yaml")
        cookie = core4.base.cookie.Cookie("test.test2")
        cookie.set("int", 2)
        self.assertEqual(cookie.get("int"), 2)
        cookie.set("str", "ene mene mu")
        self.assertEqual(cookie.get("str"), "ene mene mu")



    def testInc(self):
        os.environ["CORE4_CONFIG"] = tests.util.asset("config/local7.yaml")
        cookie = core4.base.cookie.Cookie("test.test2")
        cookie.set("int", 2)
        cookie.inc("int", 4)
        self.assertEqual(cookie.get("int"), 6)


    def testDec(self):
        os.environ["CORE4_CONFIG"] = tests.util.asset("config/local7.yaml")
        cookie = core4.base.cookie.Cookie("test.test2")
        cookie.set("int", 2)
        cookie.dec("int", 4)
        self.assertEqual(cookie.get("int"), -2)