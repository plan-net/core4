import unittest

import pymongo

import core4.base.cookie
import core4.config
import tests.util


class TestCookie(unittest.TestCase):

    def setUp(self):
        conn = pymongo.MongoClient('mongodb://core:654321@localhost:27017')
        conn.drop_database("core4test")

    @property
    def mongo(self):
        conn = pymongo.MongoClient('mongodb://core:654321@localhost:27017')
        return conn["core4test"]["sys.cookie"]

    def tearDown(self):
        tests.util.drop_env()

    def test_set(self):
        cookie = core4.base.cookie.Cookie("test.test2", self.mongo)
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

    def test_inc(self):
        cookie = core4.base.cookie.Cookie("test.test2", self.mongo)
        cookie.set("int", 2)
        cookie.inc("int", 4)
        self.assertEqual(cookie.get("int"), 6)

    def test_dec(self):
        cookie = core4.base.cookie.Cookie("test.test2", self.mongo)
        cookie.set("int", 2)
        cookie.dec("int", 4)
        self.assertEqual(cookie.get("int"), -2)

    def test_max(self):
        cookie = core4.base.cookie.Cookie("test.test2", self.mongo)
        cookie.set("max", 4)
        cookie.max("max", 8)
        self.assertEqual(cookie.get("max"), 8)
        cookie.max("max", 2)
        self.assertEqual(cookie.get("max"), 8)

    def test_min(self):
        cookie = core4.base.cookie.Cookie("test.test2", self.mongo)
        cookie.set("min", 4)
        cookie.min("min", 8)
        self.assertEqual(cookie.get("min"), 4)
        cookie.min("min", 2)
        self.assertEqual(cookie.get("min"), 2)

    def test_del(self):
        cookie = core4.base.cookie.Cookie("test.test2", self.mongo)
        cookie.set("del", 4)
        self.assertEqual(cookie.get("del"), 4)
        self.assertTrue(cookie.delete("del"))
        self.assertEqual(cookie.get("del"), None)

    def test_del_unknown(self):
        cookie = core4.base.cookie.Cookie("test.test2", self.mongo)
        self.assertFalse(cookie.delete("del"))
        self.assertEqual(cookie.get("del"), None)

    def test_has_key(self):
        cookie = core4.base.cookie.Cookie("test.test2", self.mongo)
        cookie.set("has", 4)
        self.assertEqual(cookie.has_key("has"), True)
        self.assertEqual(cookie.has_key("not_present"), False)


if __name__ == '__main__':
    unittest.main(exit=False)
