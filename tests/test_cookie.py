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
        cookie.set(first=1, second=2, third=3)
        self.assertEqual(cookie.get("first"), 1)
        self.assertEqual(cookie.get("second"), 2)
        self.assertEqual(cookie.get("third"), 3)

        with self.assertRaises(RuntimeError):
            cookie.set("z", 2, kwargs={"a": "No kwargs allowed."})



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

    def testMax(self):
        os.environ["CORE4_CONFIG"] = tests.util.asset("config/local7.yaml")
        cookie = core4.base.cookie.Cookie("test.test2")
        cookie.set("max", 4)
        cookie.max("max", 8)
        self.assertEqual(cookie.get("max"), 8)
        cookie.max("max", 2)
        self.assertEqual(cookie.get("max"), 8)

    def testMin(self):
        os.environ["CORE4_CONFIG"] = tests.util.asset("config/local7.yaml")
        cookie = core4.base.cookie.Cookie("test.test2")
        cookie.set("min", 4)
        cookie.min("min", 8)
        self.assertEqual(cookie.get("min"), 4)
        cookie.min("min", 2)
        self.assertEqual(cookie.get("min"), 2)

    def testDel(self):
        os.environ["CORE4_CONFIG"] = tests.util.asset("config/local7.yaml")
        cookie = core4.base.cookie.Cookie("test.test2")
        cookie.set("del", 4)
        self.assertEqual(cookie.get("del"), 4)
        cookie.delete("del")
        self.assertEqual(cookie.get("del"), None)

    def testhas_option(self):
        os.environ["CORE4_CONFIG"] = tests.util.asset("config/local7.yaml")
        cookie = core4.base.cookie.Cookie("test.test2")
        cookie.set("has", 4)
        self.assertEqual(cookie.has_option("has"), True)
        self.assertEqual(cookie.has_option("not_present"), False)

