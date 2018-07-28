# -*- coding: utf-8 -*-

import unittest
from pprint import pprint
import core4.error
import os
import pymongo
import pymongo.errors
import core4.api.v1.role
import re


class TestRole(unittest.TestCase):

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
        os.environ[
            "CORE4_OPTION_mongo_database"] = "core4test"

    @property
    def mongo(self):
        return pymongo.MongoClient('mongodb://core:654321@localhost:27017')

    def test_simple(self):
        r = core4.api.v1.role.Role(rolename="test", realname="test role")
        self.assertEqual(r.rolename, "test")

    def test_create(self):
        role1 = core4.api.v1.role.Role(rolename="test",
                                       realname="test role")
        role1.save()
        role2 = core4.api.v1.role.Role(rolename="another",
                                       realname="another test role")
        role2.save()
        self.assertNotEqual(role1, role2)

    def test_find(self):
        role1 = core4.api.v1.role.Role(rolename="test1",
                                       realname="test role 1   ")
        role1.save()
        role2 = core4.api.v1.role.Role(rolename="test-2",
                                       realname="test role 2 ")
        role2.save()
        role3 = core4.api.v1.role.Role(rolename="test_3",
                                       realname="test role 3")
        role3.save()
        role4 = core4.api.v1.role.Role(rolename="test_4",
                                       realname="test role 4")
        role4.save()
        data = list(core4.api.v1.role.Role().load(rolename=re.compile(".*1.*")))
        self.assertEqual(1, len(data))
        self.assertEqual(data[0].rolename, "test1")
        self.assertEqual(data[0].realname, "test role 1")
        data = list(core4.api.v1.role.Role().load())
        self.assertEqual(4, len(data))

    def test_duplicate(self):
        role1 = core4.api.v1.role.Role(rolename="test", realname="test role")
        role1.save()
        self.assertIsNotNone(role1._id)
        self.assertRaises(pymongo.errors.DuplicateKeyError,
                          core4.api.v1.role.Role(rolename="test",
                                                 realname="test role").save)
        role2 = core4.api.v1.role.Role(rolename="another",
                                       realname="another test role")
        role2.save()
        self.assertIsNotNone(role2._id)

    def test_update(self):
        role1 = core4.api.v1.role.Role(rolename="test", realname="test role")
        role1.save()
        role1 = core4.api.v1.role.Role().load_one(rolename="test")
        self.assertEqual(role1.realname, "test role")
        role1.realname = "Test Role"
        role1.save()
        role1 = core4.api.v1.role.Role().load_one(rolename="test")
        self.assertEqual(role1.realname, "Test Role")

        role1.realname = "TEST ROLE"
        role1.save()

        role1 = core4.api.v1.role.Role().load_one(rolename="test")
        self.assertEqual(role1.realname, "TEST ROLE")

        role2 = list(core4.api.v1.role.Role().load(rolename=re.compile("test.*")))
        self.assertEqual(role1.rolename, "test")
        self.assertEqual(role2[0].rolename, "test")
        #self.assertEqual(role2.rolename, "test")
        role3 = core4.api.v1.role.Role().load_one(rolename=re.compile("test.*"))
        self.assertEqual(role3.rolename, "test")

    def test_cmp(self):
        for i in range(1, 10):
            role = core4.api.v1.role.Role(rolename="test-%d" %(i),
                                           realname="test role %d" %(i))
            role.save()
        role3 = core4.api.v1.role.Role().load_one(rolename="test-3")
        role7 = core4.api.v1.role.Role().load_one(rolename="test-7")
        rolex = core4.api.v1.role.Role().load_one(rolename="test-7")
        self.assertEqual(role7, rolex)
        self.assertTrue(role3 < role7)
        self.assertFalse(role3 > role7)
        self.assertFalse(role3 == None)
        self.assertFalse(None == role3)
        self.assertTrue(role3 != None)
        self.assertTrue(None != role3)

    def test_conflict(self):
        role1 = core4.api.v1.role.Role(rolename="test", realname="test role 1")
        role1.save()

        role2 = core4.api.v1.role.Role().load_one(rolename="test")

        self.assertEqual(role1.etag, role2.etag)

        role1.is_active = False
        role1.save()

        self.assertNotEqual(role1.etag, role2.etag)
        self.assertRaises(core4.error.Core4ConflictError, role2.save)

    def test_types(self):
        self.assertRaises(
            TypeError,
            core4.api.v1.role.Role(rolename=123, realname="test role 1").save
        )
        self.assertRaises(
            TypeError,
            core4.api.v1.role.Role(realname="test role 1").save
        )
        self.assertRaises(
            TypeError,
            core4.api.v1.role.Role(rolename="123", realname=123).save
        )
        self.assertRaises(
            TypeError,
            core4.api.v1.role.Role(
                rolename="123", realname="123", is_active=1
            ).save
        )
        self.assertRaises(
            TypeError,
            core4.api.v1.role.Role(
                rolename="123", realname="123", is_active=True, perm=123
            ).save
        )

    def test_perm_protocol(self):
        core4.api.v1.role.Role(
            rolename="123", realname="123", is_active=True, perm=[
                "job://bla/r",
                "api://bla",
                "app://bla",
                "mongodb://bla"
            ]
        ).save()
        self.assertRaises(
            TypeError,
            core4.api.v1.role.Role(
                rolename="1234", realname="123", is_active=True, perm=[
                    "mongodb:/bla"]
            ).save
        )
        self.assertRaises(
            TypeError,
            core4.api.v1.role.Role(
                rolename="1234", realname="123", is_active=True, perm=[
                    "api://"]
            ).save
        )
        self.assertRaises(
            TypeError,
            core4.api.v1.role.Role(
                rolename="1234", realname="123", is_active=True, perm=[
                    "job://abc/def"]
            ).save
        )
        core4.api.v1.role.Role(
            rolename="1234", realname="123", is_active=True, perm=[
                "job://a/b/c/d/e/r",
                "job://a/b/c/d/e/x"
            ]
        ).save()

    def test_whitespace(self):
        self.assertRaises(
            TypeError,
            core4.api.v1.role.Role(
                rolename="12 34", realname="123", is_active=True, perm=[
                    "job://a/b/c/d/e/r",
                    "job://a/b/c/d/e/x"
                ]
            ).save
        )
        self.assertRaises(
            TypeError,
            core4.api.v1.role.Role(
                rolename="1234", realname="123", is_active=True, perm=[
                    "job://a /b/c/d/e/r",
                ]
            ).save
        )
        self.assertRaises(
            TypeError,
            core4.api.v1.role.Role(
                rolename="1234", realname="123", is_active=True, perm=[
                    "mongodb:// ",
                ]
            ).save
        )

    def test_login(self):
        role = core4.api.v1.role.Role(rolename="test", realname="test role")
        role.save()
        self.assertTrue(role.is_active)
        role.is_active = False
        self.assertFalse(role.is_active)
        role.is_active = True
        self.assertTrue(role.is_active)
        #self.assertEqual(role.get_id(), str(role._id))
        #self.assertFalse(role.is_admin())
        role.perm = ["cop"]
        role.save()
        #self.assertTrue(role.is_admin())
        #self.assertFalse(role.is_anonymous)
        #self.assertTrue(role.is_authenticated)

    def test_roles(self):
        test1 = core4.api.v1.role.Role(rolename="test1", realname="test role")
        test1.save()
        test2 = core4.api.v1.role.Role(rolename="test2", realname="test role",
                                       role=[test1])
        test2.save()
        test3 = core4.api.v1.role.Role(rolename="test3", realname="test role",
                                       role=[test1._id, test2])
        test3.save()

        test3.role = [test1, test2, test3]
        self.assertRaises(RuntimeError, test3.save)

        test1.role = [test2]
        self.assertRaises(RuntimeError, test1.save)

        test0 = core4.api.v1.role.Role(rolename="test0", realname="test role")
        test1.role = [test0]
        self.assertRaises(RuntimeError, test1.save)

        role = core4.api.v1.role.Role().load_one(rolename="test3")

        def traverse(r, level=0):
            #print("{}{}".format(" "*(2*level), r.rolename))
            for i in r.role:
                traverse(i, level+1)
        traverse(role)

        self.assertEqual("test1", role.role[0].rolename)
        self.assertEqual("test2", role.role[1].rolename)
        self.assertEqual("test1", role.role[1].role[0].rolename)

        test3.role = [test1._id]
        test3.save()

        role = core4.api.v1.role.Role().load_one(rolename="test3")

        self.assertEqual("test1", role.role[0].rolename)
        self.assertEqual(1, len(role.role))

    def test_delete(self):
        test1 = core4.api.v1.role.Role(rolename="test1", realname="test role")
        test1.save()
        test2 = core4.api.v1.role.Role(rolename="test2", realname="test role",
                                       role=[test1])
        test2.save()
        test3 = core4.api.v1.role.Role(rolename="test3", realname="test role",
                                       role=[test1._id, test2])
        test3.save()

        roles = list(core4.api.v1.role.Role().load())
        self.assertEqual(3, len(roles))

        test1.delete()

        roles = list(core4.api.v1.role.Role().load())
        self.assertEqual("test2", roles[0].rolename)
        self.assertEqual([], [r.rolename for r in roles[0].role])
        self.assertEqual("test3", roles[1].rolename)
        self.assertEqual(["test2"], [r.rolename for r in roles[1].role])

        self.assertEqual(2, len(roles))

        test3.role = [test1]
        self.assertRaises(RuntimeError, test3.save)
        self.assertRaises(core4.error.Core4ConflictError, test1.save)

        test1 = core4.api.v1.role.Role(rolename="test1", realname="test role",
                                       role=["test2", "test3"])
        test1.save()
        self.assertEqual(["test2", "test3"],
                         sorted([r.rolename for r in test1.role]))

    def test_delete_conflict(self):
        test1 = core4.api.v1.role.Role(rolename="test1", realname="test role")
        self.assertTrue(test1.save())
        self.assertFalse(test1.save())
        test2 = core4.api.v1.role.Role().load_one(rolename="test1")
        self.assertFalse(test2.save())
        test2.realname = "change"
        self.assertTrue(test2.save())
        self.assertFalse(test2.save())
        test2.realname = "change1"
        self.assertTrue(test2.save())
        self.assertFalse(test2.save())
        test = core4.api.v1.role.Role().load_one(rolename="test1")
        self.assertEqual(test, test2)
        self.assertNotEqual(test1, test2)
        self.assertRaises(core4.error.Core4ConflictError, test1.delete)

    def test_objectid(self):
        test1 = core4.api.v1.role.Role(rolename="test1", realname="test role")
        self.assertTrue(test1.save())

        test = core4.api.v1.role.Role().load_one(rolename="test1")
        test._id = "abc"
        self.assertRaises(TypeError, test.save)

        test = core4.api.v1.role.Role().load_one(rolename="test1")
        test.created = "abc"
        test.save()

        test.etag = "abc"
        self.assertRaises(TypeError, test.save)
        #self.assertRaises(TypeError, test.save)

    def test_repr(self):
        test1 = core4.api.v1.role.Role(rolename="test1", realname="test role")
        self.assertTrue(repr(test1).startswith("core4.api.v1.role.Role("))
        self.assertRaises(RuntimeError, test1.delete)
        test = core4.api.v1.role.Role().load_one(rolename="test1")
        self.assertIsNone(test)
        test1.save()
        test = core4.api.v1.role.Role().load_one(rolename="test1")
        self.assertIsNotNone(test)

    # def test_user(self):
    #     test = core4.api.v1.role.Role(rolename="test1", realname="test role",
    #                                   password=123)
    #     self.assertRaises(TypeError, test.save)
    #     test = core4.api.v1.role.Role(rolename="test1", realname="test role",
    #                                   password=123)
    #     self.assertRaises(TypeError, test.save)
    #     test = core4.api.v1.role.Role(rolename="test1", realname="test role",
    #                                   password="m")
    #     self.assertRaises(AttributeError, test.save)
    #     test = core4.api.v1.role.Role(rolename="test1", realname="test role",
    #                                   email="m")
    #     self.assertRaises(TypeError, test.save)
    #     test = core4.api.v1.role.Role(rolename="test1", realname="test role",
    #                                   email="m@a")
    #     self.assertRaises(TypeError, test.save)
    #     test = core4.api.v1.role.Role(rolename="test1", realname="test role",
    #                                   email="m@a.de")
    #     self.assertRaises(AttributeError, test.save)
    #     test = core4.api.v1.role.Role(rolename="test1", realname="test role",
    #                                   email=123)
    #     self.assertRaises(TypeError, test.save)
    #     test = core4.api.v1.role.Role(rolename="test1", realname="test role",
    #                                   email="m@a.de", password="123")
    #     test.save()
    #
    # def test_rename(self):
    #     test1 = core4.api.v1.role.Role(rolename="test1", realname="test role",
    #                                   password="123456", email="a@b.cd")
    #     test1.save()
    #     test2 = core4.api.v1.role.Role(rolename="test2", realname="test role",
    #                                    password="123456", email="a@b.cd")
    #     test2.save()
    #
    #     test1.rolename = "test2"
    #     self.assertTrue(isinstance(test1, core4.api.v1.role.Role))
    #     self.assertRaises(AttributeError, lambda: test1.update)
    #     self.assertRaises(pymongo.errors.DuplicateKeyError, test1.save)
    #
    # def test_new_password(self):
    #     test1 = core4.api.v1.role.Role(rolename="test1", realname="test role",
    #                                    password="123456", email="a@b.cd")
    #     test1.save()
    #     test1.password = "654321"
    #     test1.save()
    #
    #     test2 = core4.api.v1.role.Role().load_one(rolename="test1")
    #     self.assertTrue(test2.verify_password("654321"))
    #     self.assertFalse(test2.verify_password("123456"))
    #
    #     test3 = core4.api.v1.role.Role(rolename="test2", realname="test role")
    #     test3.save()
    #     test3.password = "654321"
    #     self.assertRaises(AttributeError, test3.save)
    #
    #     test4 = core4.api.v1.role.Role().load_one(rolename="test2")
    #     self.assertFalse(test4.verify_password("654321"))
    #     self.assertFalse(test4.verify_password("123456"))
    #     data = list(self.mongo.core4test.sys.role.find())
    #     self.assertEqual([], [i for i in data if "password_hash" in i])

if __name__ == '__main__':
    unittest.main()
