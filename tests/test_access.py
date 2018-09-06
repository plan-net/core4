# -*- coding: utf-8 -*-

import os
import unittest

import pymongo
import pymongo.errors

import core4.api.v1.role.main
import core4.error
import core4.service.access.manager
import core4.service.access.handler.mongo
import core4.util
from tests.test_logger import LogOn


class TestAccess(unittest.TestCase):

    def setUp(self):
        self.tearDown()
        self.tearup()

    def tearup(self):
        os.environ[
            "CORE4_OPTION_DEFAULT__mongo_url"] = "mongodb://core:654321@localhost:27017"
        os.environ[
            "CORE4_OPTION_DEFAULT__mongo_database"] = "core4test"
        mongo = self.mongo()
        LogOn()
        for i in range(1, 5):
            db = "core4test" + str(i)
            for j in range(i):
                mongo[db].coll1.insert_one({})
            for j in range(i*2):
                mongo[db].coll2.insert_one({})

    def tearDown(self):
        mongo = self.mongo()
        for db in ["core4test"] + ["core4test" + str(i) for i in range(1, 5)]:
            mongo.drop_database(db)
        for db in mongo.database_names():
            if db.startswith("user!regress_"):
                mongo.drop_database(db)
        users = mongo.admin.command("usersInfo")
        for user in users["users"]:
            if user["user"].startswith("regress_"):
                mongo.admin.command('dropUser', user["user"])
        roles = mongo.admin.command("rolesInfo")
        for role in roles["roles"]:
            if role["role"].startswith("regress_"):
                mongo.admin.command('dropRole', role["role"])
        dels = []
        for k in os.environ:
            if k.startswith('CORE4_'):
                dels.append(k)
        for k in dels:
            del os.environ[k]

    @classmethod
    def tearDownClass(cls):
        cls.tearDown(cls)

    @staticmethod
    def mongo():
        return pymongo.MongoClient('mongodb://core:654321@localhost:27017')

    def test_simple(self):
        test_role = core4.api.v1.role.main.Role(
            name="regress_test", realname="test role", email="test@role.de",
            password="123456", perm=["mongodb://core4test1"])
        test_role.save()
        role = core4.api.v1.role.Role(name="regress_test").load_one()
        self.assertTrue(role.verify_password("123456"))
        self.assertEqual(role.realname, "test role")

    def test_manager(self):
        test_role = core4.api.v1.role.main.Role(
            name="regress_test", realname="test role", email="test@role.de",
            password="123456", perm=["mongodb://core4test1"])
        test_role.save()
        m1 = core4.service.access.manager.CoreAccessManager("regress_test")
        role = core4.api.v1.role.Role(name="regress_test").load_one()
        m2 = core4.service.access.manager.CoreAccessManager(role)
        self.assertEqual(m1.role, m2.role)

    def test_token(self):
        test_role = core4.api.v1.role.main.Role(
            name="regress_test", realname="test role", email="test@role.de",
            password="123456", perm=["mongodb://core4test1"])
        test_role.save()
        role = core4.api.v1.role.Role().load_one(name="regress_test")
        handler = core4.service.access.handler.mongo.MongoHandler(role)
        token = handler.create_token()
        self.assertEqual(len(token),
                         core4.service.access.handler.mongo.PASSWORD_LENGTH)

    def test_mere_role(self):
        test_role = core4.api.v1.role.main.Role(
            name="regress_test", realname="test role",
            perm=["mongodb://core4test1"])
        test_role.save()
        role = core4.api.v1.role.Role().load_one(name="regress_test")
        self.assertRaises(core4.error.Core4UsageError,
                          core4.service.access.manager.CoreAccessManager, role)
        self.assertRaises(core4.error.Core4UsageError,
                          core4.service.access.manager.CoreAccessManager,
                          "regress_test")
        self.assertRaises(StopIteration,
                          core4.service.access.manager.CoreAccessManager,
                          "notexist")

    def test_add_role(self):
        test_role = core4.api.v1.role.main.Role(
            name="regress_test", realname="test role", email="test@role.de",
            password="123456", perm=["mongodb://core4test1"])
        test_role.save()
        mgr = core4.service.access.manager.CoreAccessManager("regress_test")
        access = mgr.synchronise()
        token = access["mongodb"]
        connection = pymongo.MongoClient(
            'mongodb://{}:{}@localhost:27017'.format("regress_test", token))
        self.assertEqual(1, connection.core4test1.coll1.count())
        self.assertEqual(2, connection.core4test1.coll2.count())
        for i in range(2, 5):
            db = "core4test" + str(i)
            self.assertRaises(pymongo.errors.OperationFailure,
                              connection[db].coll1.count)
            self.assertRaises(pymongo.errors.OperationFailure,
                              connection[db].coll2.count)

    def test_update_role(self):
        test_role = core4.api.v1.role.main.Role(
            name="regress_test", realname="test role", email="test@role.de",
            password="123456", perm=["mongodb://core4test1"])
        test_role.save()
        mgr = core4.service.access.manager.CoreAccessManager("regress_test")
        access = mgr.synchronise()
        token = access["mongodb"]
        connection = pymongo.MongoClient(
            'mongodb://{}:{}@localhost:27017'.format("regress_test", token))
        self.assertEqual(1, connection.core4test1.coll1.count())
        self.assertEqual(2, connection.core4test1.coll2.count())
        self.assertRaises(pymongo.errors.OperationFailure,
                          connection.core4test2.coll1.count)
        self.assertRaises(pymongo.errors.OperationFailure,
                          connection.core4test2.coll2.count)
        test_role.perm = ["mongodb://core4test1", "mongodb://core4test2"]
        test_role.save()
        mgr = core4.service.access.manager.CoreAccessManager("regress_test")
        access = mgr.synchronise()
        token = access["mongodb"]
        connection = pymongo.MongoClient(
            'mongodb://{}:{}@localhost:27017'.format("regress_test", token))
        self.assertEqual(1, connection.core4test1.coll1.count())
        self.assertEqual(2, connection.core4test1.coll2.count())
        self.assertEqual(2, connection.core4test2.coll1.count())
        self.assertEqual(4, connection.core4test2.coll2.count())

    def test_multi_db(self):
        test_role = core4.api.v1.role.main.Role(
            name="regress_test", realname="test role", email="test@role.de",
            password="123456", perm=["mongodb://core4test1",
                                     "mongodb://core4test2"])
        test_role.save()
        mgr = core4.service.access.manager.CoreAccessManager("regress_test")
        access = mgr.synchronise()
        token = access["mongodb"]
        connection = pymongo.MongoClient(
            'mongodb://{}:{}@localhost:27017'.format("regress_test", token))
        self.assertEqual(1, connection.core4test1.coll1.count())
        self.assertEqual(2, connection.core4test1.coll2.count())
        self.assertEqual(2, connection.core4test2.coll1.count())
        self.assertEqual(4, connection.core4test2.coll2.count())
        for i in range(3, 5):
            db = "core4test" + str(i)
            self.assertRaises(pymongo.errors.OperationFailure,
                              connection[db].coll1.count)
            self.assertRaises(pymongo.errors.OperationFailure,
                              connection[db].coll2.count)

    def test_duplicate(self):
        test_role1 = core4.api.v1.role.main.Role(
            name="regress_test1", realname="test role", email="test1@role.de",
            password="123456", perm=["mongodb://core4test1",
                                     "mongodb://core4test2"])
        test_role1.save()
        test_role2 = core4.api.v1.role.main.Role(
            name="regress_test1", realname="test role", email="test2@role.de",
            password="654321")
        self.assertRaises(pymongo.errors.DuplicateKeyError, test_role2.save)

        test_role2 = core4.api.v1.role.main.Role(
            name="regress_test2", realname="test role", email="test1@role.de",
            password="654321")
        self.assertRaises(pymongo.errors.DuplicateKeyError, test_role2.save)

        test_role2 = core4.api.v1.role.main.Role(
            name="regress_test2", realname="test role", email="test2@role.de",
            password="654321")
        test_role2.save()

    def test_user_db(self):
        test_role1 = core4.api.v1.role.main.Role(
            name="regress_test1", realname="test role", email="test1@role.de",
            password="123456", perm=["mongodb://core4test1",
                                     "mongodb://core4test2"])
        test_role1.save()
        test_role2 = core4.api.v1.role.main.Role(
            name="regress_test2", realname="test role", email="test2@role.de",
            password="654321")
        test_role2.save()

        mgr = core4.service.access.manager.CoreAccessManager("regress_test1")
        access = mgr.synchronise()
        token = access["mongodb"]

        connection = pymongo.MongoClient(
            'mongodb://{}:{}@localhost:27017'.format("regress_test1", token))
        self.assertEqual(0, connection["user!regress_test1"].coll.count())
        connection["user!regress_test1"].coll.insert_one({})
        self.assertEqual(1, connection["user!regress_test1"].coll.count())

        self.assertRaises(pymongo.errors.OperationFailure,
                          connection["user!regress_test2"].coll.count)

        mgr = core4.service.access.manager.CoreAccessManager("regress_test2")
        access = mgr.synchronise()
        token = access["mongodb"]

        connection = pymongo.MongoClient(
            'mongodb://{}:{}@localhost:27017'.format("regress_test2", token))
        self.assertEqual(0, connection["user!regress_test2"].coll.count())
        connection["user!regress_test2"].coll.insert_one({})
        connection["user!regress_test2"].coll.insert_one({})
        self.assertEqual(2, connection["user!regress_test2"].coll.count())

        self.assertRaises(pymongo.errors.OperationFailure,
                          connection["user!regress_test1"].coll.count)

    def test_dependency(self):
        test_role1 = core4.api.v1.role.main.Role(
            name="regress_test1", realname="test role", email="test1@role.de",
            password="123456", perm=["mongodb://core4test1",
                                     "mongodb://core4test2"])
        test_role1.save()
        test_role2 = core4.api.v1.role.main.Role(
            name="regress_test2", realname="test role", email="test2@role.de",
            password="654321", role=[test_role1])
        test_role2.save()
        mgr = core4.service.access.manager.CoreAccessManager("regress_test1")
        mgr.synchronise()
        mgr = core4.service.access.manager.CoreAccessManager("regress_test2")
        #print(mgr.synchronise())


if __name__ == '__main__':
    unittest.main()
