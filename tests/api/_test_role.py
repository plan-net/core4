# -*- coding: utf-8 -*-

import os
import re
import unittest

import pymongo
import pymongo.errors
from bson.objectid import ObjectId
from flask import Flask
from flask_login import LoginManager

import core4.api.v1.role.main
import core4.error
import core4.util
import core4.util.node
import tests.util

class LogOn(core4.base.CoreBase, core4.logger.CoreLoggerMixin):

    cache = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_logging()


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
            "CORE4_OPTION_DEFAULT__mongo_url"] = "mongodb://core:654321@localhost:27017"
        os.environ[
            "CORE4_OPTION_DEFAULT__mongo_database"] = "core4test"
        os.environ["CORE4_CONFIG"] = tests.util.asset("config/empty.yaml")
        LogOn()

    def tearDown(self):
        tests.util.drop_env()

    @property
    def mongo(self):
        return pymongo.MongoClient('mongodb://core:654321@localhost:27017')

    def test_simple(self):
        r1 = core4.api.v1.role.main.Role(name="test", realname="test role")
        self.assertIn("name='test'", repr(r1))
        r2 = core4.api.v1.role.main.Role()
        self.assertIn("name=None", repr(r2))

    def test_kwargs(self):
        self.assertRaises(TypeError, core4.api.v1.role.main.Role,
                          **dict(unknown="test"))

    def test_validate(self):
        self.assertRaises(TypeError, core4.api.v1.role.main.Role,
                          **dict(name=123))
        # self.assertRaises(TypeError, r1.save)
        r1 = core4.api.v1.role.main.Role(name="123")
        self.assertTrue(r1.is_active)
        self.assertRaises(TypeError, core4.api.v1.role.main.Role, **dict(
            name="123", is_active=123))
        self.assertRaises(TypeError, core4.api.v1.role.main.Role,
                          **dict(name="    "))

    def test_empty_name(self):
        r1 = core4.api.v1.role.main.Role(realname="GOOD")
        self.assertRaises(TypeError, r1.save)

    def test_timestamp(self):
        r1 = core4.api.v1.role.main.Role(name="GOOD")
        r1.save()
        self.assertIsNotNone(r1.created)
        self.assertIsNone(r1.updated)

        def t():
            r1.created = 123

        self.assertRaises(TypeError, t)

    def test_unknown_attribute(self):
        r1 = core4.api.v1.role.main.Role(name="master", role=[])
        self.assertRaises(AttributeError, lambda: r1.bla)

    def test_conflict(self):
        role1 = core4.api.v1.role.main.Role(name="test",
                                            realname="test role 1")
        role1.save()

        role2 = core4.api.v1.role.main.Role().load_one(name="test")

        self.assertEqual(role1.etag, role2.etag)

        role1.is_active = False
        role1.save()

        self.assertNotEqual(role1.etag, role2.etag)
        self.assertRaises(core4.error.Core4ConflictError, role2.save)

    def test_role(self):
        self.assertRaises(TypeError, core4.api.v1.role.main.Role,
                          **dict(name="master", role=[1, 2, 3]))
        self.assertRaises(TypeError, core4.api.v1.role.main.Role,
                          **dict(name="master", role=1))
        # self.assertRaises(TypeError, r1.save)
        r1 = core4.api.v1.role.main.Role(name="master", role=[])
        r1.save()
        r2 = core4.api.v1.role.main.Role(name="slave", role=[r1, r1._id])
        r2.save()
        self.assertEqual(r2.role[0]._id, r1._id)
        self.assertRaises(
            core4.error.Core4RoleNotFound, core4.api.v1.role.main.Role, **dict(
                name="slave", role=[r1, ObjectId("5b5e9ee134ed091e06430425")]))
        # self.assertRaises(core4.error.Core4RoleNotFound, r3.save)

    def test_user(self):
        r = core4.api.v1.role.main.Role(name="role1", password="hello")
        self.assertRaises(AttributeError, r.save)
        r = core4.api.v1.role.main.Role(name="role1", email="a@b.cd")
        self.assertRaises(AttributeError, r.save)
        r = core4.api.v1.role.main.Role(name="role1", email="a@b.cd",
                                        password="hello")
        r.save()
        self.assertRaises(TypeError, core4.api.v1.role.main.Role,
                          **dict(name="role1", email="a@b.c",
                                 password="hello"))
        self.assertRaises(TypeError, core4.api.v1.role.main.Role,
                          **dict(name="role1", email="@b.cd",
                                 password="hello"))
        # self.assertRaises(TypeError, r.save)
        # self.assertRaises(TypeError, r.save)

    def test_load(self):
        for i in range(1, 11):
            r = core4.api.v1.role.main.Role(name="role%d" % (i))
            r.save()
        for i in range(11, 16):
            r = core4.api.v1.role.main.Role(name="role%d" % (i),
                                            email="mail-%d@test.de" % (i),
                                            password="hello-%d" % (i))
            r.save()
        ret = list(core4.api.v1.role.main.Role().load())
        self.assertEqual(15, len(ret))
        ret = list(core4.api.v1.role.main.Role().load(user=True))
        self.assertEqual(5, len(ret))
        ret = list(core4.api.v1.role.main.Role().load(role=True))
        self.assertEqual(10, len(ret))
        ret = list(core4.api.v1.role.main.Role().load(role=True, user=True))
        self.assertEqual(15, len(ret))

    def test_password_type(self):
        self.assertRaises(TypeError, core4.api.v1.role.main.Role,
                          **dict(name="roled", email="mail@test.de",
                                 password=True))

    def test_load_one(self):
        self.assertRaises(StopIteration,
                          core4.api.v1.role.main.Role().load_one)

    def test_password(self):
        r = core4.api.v1.role.main.Role(name="role1", email="a@b.cd",
                                        password="hello")
        r.save()
        doc = core4.api.v1.role.main.Role().load_one()
        self.assertIsNotNone(doc.data["password"].value)
        self.assertTrue(doc.verify_password("hello"))

    def test_equal(self):
        r1 = core4.api.v1.role.main.Role(name="role1", email="a@b.cd",
                                         password="hello")
        r1.save()
        r2 = core4.api.v1.role.main.Role().load_one()
        self.assertEqual(r1, r2)
        r1 = core4.api.v1.role.main.Role(name="role2", email="a@b.cd",
                                         password="hello")
        r2 = core4.api.v1.role.main.Role(name="role2", email="a@b.cd",
                                         password="hello")
        self.assertNotEqual(r1, r2)

    def test_password_update(self):
        r = core4.api.v1.role.main.Role(name="role1", email="a@b.cd",
                                        password="hello")
        self.assertIsNone(r.etag)
        r.save()
        self.assertIsNotNone(r.etag)
        doc = core4.api.v1.role.main.Role().load_one()
        self.assertIsNotNone(doc.data["password"])
        self.assertTrue(doc.verify_password("hello"))
        doc.password = "123456"
        doc.save()
        self.assertTrue(doc.verify_password("123456"))
        doc = core4.api.v1.role.main.Role().load_one()
        self.assertIsNotNone(doc.data["password"].value)
        self.assertTrue(doc.verify_password("123456"))

    def test_unique(self):
        r1 = core4.api.v1.role.main.Role(name="role1", role=[])
        r1.save()
        r2 = core4.api.v1.role.main.Role(name="role1", role=[])
        self.assertRaises(pymongo.errors.DuplicateKeyError, r2.save)
        r3 = core4.api.v1.role.main.Role(name="role2", role=[])
        r3.save()
        r3.name = "role3"
        r3.save()
        e1 = r3.etag
        doc = core4.api.v1.role.main.Role().load_one(name="role3")
        self.assertEqual(doc.name, "role3")
        r3.name = "role3"
        r3.save()
        e2 = r3.etag
        self.assertEqual(e2, e1)

    def test_no_change(self):
        r1 = core4.api.v1.role.main.Role(name="role1", email="a@b.cd",
                                         password="hello")
        r1.save()
        etag = r1.etag
        doc = core4.api.v1.role.main.Role().load_one()
        doc.password = "hello"
        doc.save()
        self.assertNotEqual(etag, doc.etag)
        etag = doc.etag
        doc.name = "role1"
        doc.save()
        self.assertEqual(etag, doc.etag)
        etag = doc.etag
        doc.name = "role2"
        doc.save()
        self.assertNotEqual(etag, doc.etag)
        etag = doc.etag
        doc.name = "role2"
        doc.save()
        self.assertEqual(etag, doc.etag)
        etag = doc.etag
        doc.email = "d@ef.gh"
        doc.save()
        self.assertNotEqual(etag, doc.etag)
        etag = doc.etag

        def test():
            doc.email = "d@ef.g"

        self.assertRaises(TypeError, test)
        # self.assertRaises(TypeError, doc.save)

    def test_cmp(self):
        for i in range(1, 10):
            role = core4.api.v1.role.main.Role(name="test-%d" % (i),
                                               realname="test role %d" % (i))
            role.save()
        role3 = core4.api.v1.role.main.Role().load_one(name="test-3")
        role7 = core4.api.v1.role.main.Role().load_one(name="test-7")
        rolex = core4.api.v1.role.main.Role().load_one(name="test-7")
        self.assertEqual(role7, rolex)
        self.assertTrue(role3 < role7)
        self.assertFalse(role3 > role7)
        self.assertFalse(role3 == None)
        self.assertFalse(None == role3)
        self.assertTrue(role3 != None)
        self.assertTrue(None != role3)

    def test_circle(self):
        r1 = core4.api.v1.role.main.Role(name="role1", role=[])
        r1.save()
        r2 = core4.api.v1.role.main.Role(name="role2", role=[r1])
        r2.save()
        r3 = core4.api.v1.role.main.Role(name="role3", role=[r1, r2])
        r3.save()
        r2.role = [r3]
        self.assertRaises(RuntimeError, r2.save)
        r2.role = [r1]
        etag = r2.etag
        r2.save()
        self.assertEqual(etag, r2.etag)

    def test_objectId(self):
        r1 = core4.api.v1.role.main.Role(name="role1", role=[])
        r1.save()
        r1._id = ObjectId("5b5f8b6634ed095c5c6fa4f9")
        self.assertRaises(RuntimeError, r1.save)

        def t():
            r1._id = 123

        self.assertRaises(TypeError, t)

    def test_delete(self):
        test1 = core4.api.v1.role.main.Role(name="test1", realname="test role")
        test1.save()
        test2 = core4.api.v1.role.main.Role(
            name="test2", realname="test role", role=[test1])
        test2.save()
        test3 = core4.api.v1.role.main.Role(
            name="test3", realname="test role", role=[test1._id, test2])
        test3.save()

        roles = list(core4.api.v1.role.main.Role().load())
        self.assertEqual(3, len(roles))

        test1.delete()

        roles = list(core4.api.v1.role.main.Role().load())
        self.assertEqual("test2", roles[0].name)
        self.assertEqual([], [r.rolename for r in roles[0].role])
        self.assertEqual("test3", roles[1].name)
        self.assertEqual(["test2"], [r.name for r in roles[1].role])

        self.assertEqual(2, len(roles))

        def t():
            test3.role = [test1]

        self.assertRaises(TypeError, t)

        test1.save()
        test1.role = []  # 3: 2  1: 2,3
        test1.save()
        self.assertEqual([], sorted([r.rolename for r in test1.role]))

    def test_delete_conflict(self):
        test1 = core4.api.v1.role.main.Role(name="test1", realname="test role")
        self.assertTrue(test1.save())
        self.assertFalse(test1.save())
        test2 = core4.api.v1.role.main.Role().load_one(name="test1")
        self.assertFalse(test2.save())
        test2.realname = "change"
        self.assertTrue(test2.save())
        self.assertFalse(test2.save())
        test2.realname = "change1"
        self.assertTrue(test2.save())
        self.assertFalse(test2.save())
        test = core4.api.v1.role.main.Role().load_one(name="test1")
        self.assertEqual(test, test2)
        self.assertNotEqual(test1, test2)
        self.assertRaises(core4.error.Core4ConflictError, test1.delete)

    def test_create(self):
        role1 = core4.api.v1.role.main.Role(name="test", realname="test role")
        role1.save()
        role2 = core4.api.v1.role.main.Role(name="another",
                                            realname="another test role")
        role2.save()
        self.assertNotEqual(role1, role2)

    def test_find(self):
        role1 = core4.api.v1.role.main.Role(name="test1",
                                            realname="test role 1   ")
        role1.save()
        role2 = core4.api.v1.role.main.Role(name="test-2",
                                            realname="test role 2 ")
        role2.save()
        role3 = core4.api.v1.role.main.Role(name="test_3",
                                            realname="test role 3")
        role3.save()
        role4 = core4.api.v1.role.main.Role(name="test_4",
                                            realname="test role 4")
        role4.save()
        data = list(core4.api.v1.role.main.Role().load(
            name=re.compile(".*1.*")))
        self.assertEqual(1, len(data))
        self.assertEqual(data[0].name, "test1")
        self.assertEqual(data[0].realname, "test role 1")
        data = list(core4.api.v1.role.main.Role().load())
        self.assertEqual(4, len(data))

    #
    def test_duplicate(self):
        role1 = core4.api.v1.role.main.Role(name="test", realname="test role")
        role1.save()
        self.assertIsNotNone(role1._id)
        self.assertRaises(pymongo.errors.DuplicateKeyError,
                          core4.api.v1.role.main.Role(
                              name="test", realname="test role").save)
        role2 = core4.api.v1.role.main.Role(
            name="another", realname="another test role")
        role2.save()
        self.assertIsNotNone(role2._id)

    def test_update(self):
        role1 = core4.api.v1.role.main.Role(name="test", realname="test role")
        role1.save()
        role1 = core4.api.v1.role.main.Role().load_one(name="test")
        self.assertEqual(role1.realname, "test role")
        role1.realname = "Test Role"
        role1.save()
        role1 = core4.api.v1.role.main.Role().load_one(name="test")
        self.assertEqual(role1.realname, "Test Role")

        role1.realname = "TEST ROLE"
        role1.save()

        role1 = core4.api.v1.role.main.Role().load_one(name="test")
        self.assertEqual(role1.realname, "TEST ROLE")

        role2 = list(core4.api.v1.role.main.Role().load(
            name=re.compile("test.*")))
        self.assertEqual(role1.name, "test")
        self.assertEqual(role2[0].name, "test")
        # self.assertEqual(role2.rolename, "test")
        role3 = core4.api.v1.role.main.Role().load_one(
            name=re.compile("test.*"))
        self.assertEqual(role3.name, "test")

    def test_perm_protocol(self):
        t = core4.api.v1.role.main.Role(
            name="123", realname="123", is_active=True, perm=[
                "job://bla/r",
                "api://bla",
                "app://bla",
                "cop",
                "mongodb://bla"
            ]
        )
        t.save()
        self.assertRaises(
            TypeError,
            core4.api.v1.role.main.Role, **dict(
                name="1234", realname="123", is_active=True, perm=[
                    "mongodb:/bla"]
            )
        )
        self.assertRaises(
            TypeError,
            core4.api.v1.role.main.Role, **dict(
                name="1234", realname="123", is_active=True, perm=True))
        self.assertRaises(
            TypeError,
            core4.api.v1.role.main.Role, **dict(
                name="1234", realname="123", is_active=True, perm=[
                    "cops"]
            )
        )
        t = core4.api.v1.role.main.Role(
            name="1234", realname="123", is_active=True, perm=[
                "cop"
            ]
        )
        t.save()
        self.assertRaises(
            TypeError,
            core4.api.v1.role.main.Role, **dict(
                name="1234", realname="123", is_active=True, perm=[
                    "api://"]
            )
        )
        self.assertRaises(
            TypeError,
            core4.api.v1.role.main.Role, **dict(
                name="1234", realname="123", is_active=True, perm=[
                    "job://abc/def"]
            )
        )
        self.assertRaises(
            TypeError,
            core4.api.v1.role.main.Role, **dict(
                name="1234", realname="123", is_active=True, perm=[
                    "job://a/b/c/d/e/r",
                    "job://a/b/c/d/e/x"]
            )
        )

    def test_whitespace(self):
        self.assertRaises(
            TypeError,
            core4.api.v1.role.main.Role, **dict(
                name="12 34", realname="123", is_active=True, perm=[
                    "job://a.b.c.d/r",
                    "job://a.b.c.d.e/x"]
            )
        )
        core4.api.v1.role.main.Role(
            name="1234", realname="123", is_active=True, perm=[
                "job://a.b.c.d/r",
                "job://a.b.c.d.e/x"]
        )
        core4.api.v1.role.main.Role(
            name="1234", realname="123", is_active=True, perm=[
                "job://a.b.c.d/r",
                "job://a.b.c.d.e/x"]
        )
        self.assertRaises(
            TypeError,
            core4.api.v1.role.main.Role, **dict(
                name="1234", realname="123", is_active=True, perm=[
                    "job://a.b.c .d/r"]
            )
        )
        self.assertRaises(
            TypeError,
            core4.api.v1.role.main.Role, **dict(
                name="1234", realname="123", is_active=True, perm=[
                    "mongodb:// "]
            )
        )
        core4.api.v1.role.main.Role(
            name="1234", realname="123", is_active=True, perm=[
                "mongodb://abc"]
        )
        self.assertRaises(
            TypeError,
            core4.api.v1.role.main.Role, **dict(
                name="1234", realname="123", is_active=True, perm=[
                    "mongodb://"]
            )
        )
        core4.api.v1.role.main.Role(
            name="1234", realname="123", is_active=True, perm=[
                "mongodb://abc"]
        )

    def test_login(self):
        role = core4.api.v1.role.main.Role(name="test", realname="test role")
        role.save()
        self.assertTrue(role.is_active)
        role.is_active = False
        self.assertFalse(role.is_active)
        role.is_active = True
        self.assertTrue(role.is_active)
        self.assertEqual(role.get_id(), str(role._id))
        self.assertFalse(role.is_admin)
        role.perm = ["cop"]
        role.save()
        self.assertTrue(role.is_admin)
        self.assertFalse(role.is_anonymous)
        self.assertFalse(role.is_authenticated)

    def test_repr(self):
        test1 = core4.api.v1.role.main.Role(name="test1", realname="test role")
        self.assertTrue(repr(test1).startswith("core4.api.v1.role.main.Role("))
        self.assertRaises(RuntimeError, test1.delete)
        self.assertRaises(StopIteration,
                          core4.api.v1.role.main.Role().load_one,
                          name="test1")
        test1.save()
        test = core4.api.v1.role.main.Role().load_one(name="test1")
        self.assertIsNotNone(test)

    def test_cop(self):
        t1 = core4.api.v1.role.main.Role(
            name="1234", realname="123", is_active=True, perm=[
                "cop"]
        )
        self.assertTrue(t1.is_admin)
        t2 = core4.api.v1.role.main.Role(
            name="1234", realname="123", is_active=True)
        self.assertFalse(t2.is_admin)

    def test_job_access(self):
        t1 = core4.api.v1.role.main.Role(
            name="1234", realname="123", is_active=True, perm=[
                "cop"]
        )
        self.assertTrue(t1.has_job_access("test.job.TestJob"))
        t1 = core4.api.v1.role.main.Role(
            name="1234", realname="123", is_active=True, perm=[]
        )
        self.assertFalse(t1.has_job_access("test.job.TestJob"))
        t1 = core4.api.v1.role.main.Role(
            name="1234", realname="123", is_active=True, perm=[
                "job://test.job.read.*/r",
                "job://test.job.exec.*/x",
            ]
        )
        self.assertTrue(t1.has_job_access("test.job.read.TestJob"))
        self.assertFalse(t1.has_job_access("test.job.other.No"))
        self.assertFalse(t1.has_job_exec_access("test.job.read.TestJob"))
        self.assertTrue(t1.has_job_access("test.job.exec.ExecJob"))
        self.assertTrue(t1.has_job_exec_access("test.job.exec.ExecJob"))

    def test_api_access(self):
        t1 = core4.api.v1.role.main.Role(
            name="1234", realname="123", is_active=True, perm=[
                "cop"]
        )
        self.assertTrue(t1.has_api_access("test.job.TestJob"))
        t1 = core4.api.v1.role.main.Role(
            name="1234", realname="123", is_active=True, perm=[]
        )
        self.assertFalse(t1.has_api_access("test.job.TestJob"))
        t1 = core4.api.v1.role.main.Role(
            name="1234", realname="123", is_active=True, perm=[
                "api://test.job.read.*"
            ]
        )
        self.assertTrue(t1.has_api_access("test.job.read.TestJob"))
        self.assertFalse(t1.has_api_access("test.job.other.No"))

    def test_last_login(self):
        role = core4.api.v1.role.main.Role(
            name="test", realname="test_role", perm=["cop"])

        def load_user(self, id):
            _id = ObjectId(id)
            return core4.api.v1.role.main.Role().load_one(id=_id)

        role.save()
        app = Flask(__name__)
        login_manager = LoginManager()
        login_manager.init_app(app)
        login_manager.user_loader(load_user)
        app.config.update(SECRET_KEY="test key")

        self.assertIsNone(role.last_login)
        with app.app_context():
            with app.test_request_context():
                role.login()
        self.assertIsNotNone(role.last_login)

    def test_limit(self):
        core4.api.v1.role.main.Role(
            name="test", realname="test_role", quota="1:123")
        self.assertRaises(TypeError, core4.api.v1.role.main.Role, **dict(
            name="test", realname="test_role", quota="a"))
        self.assertRaises(TypeError, core4.api.v1.role.main.Role, **dict(
            name="test", realname="test_role", quota="a:abc"))
        self.assertRaises(TypeError, core4.api.v1.role.main.Role, **dict(
            name="test", realname="test_role", quota="a:abc:123"))
        test = core4.api.v1.role.main.Role(
            name="test", realname="test_role", quota="1/60")
        test.save()
        test.save()
        core4.api.v1.role.main.Role(
            name="test", realname="test_role", quota=" 1 / 60 ")

    def test_limit_counter(self):
        role = core4.api.v1.role.main.Role(
            name="test", realname="test_role", quota="10:1")
        role.save()
        for i in range(0, 5):
            t0 = core4.util.node.now()
            for i in range(10):
                role.dec_quota()
            self.assertFalse(role.dec_quota())
            while not role.dec_quota():
                t1 = core4.util.node.now()
            self.assertAlmostEqual((t1 - t0).total_seconds(), 1, 0)

    def test_limit_time(self):
        role = core4.api.v1.role.main.Role(
            name="test", realname="test_role", quota="1:1")
        role.save()
        t0 = core4.util.node.now()
        success = 5
        while success > 0:
            if role.dec_quota():
                success -= 1
        self.assertAlmostEqual((core4.util.node.now() - t0).total_seconds(), 4, 0)

    def test_perm_cascade(self):
        role1 = core4.api.v1.role.main.Role(
            name="test1", realname="test_role", perm=["app://1"])
        role1.save()
        role2 = core4.api.v1.role.main.Role(
            name="test2", realname="test_role", perm=["app://2", "app://1"])
        role2.save()
        role3 = core4.api.v1.role.main.Role(
            name="test3", realname="test_role", perm=["app://3"],
            role=[role1, role2])
        role3.save()
        self.assertEqual(role3.perm, ["app://3"])
        self.assertEqual(role3._casc_perm, ["app://1", "app://2", "app://3"])

    def test_perm_recursion(self):
        role1 = core4.api.v1.role.main.Role(
            name="test1", realname="test_role", perm=["app://1"])
        role1.save()
        role2 = core4.api.v1.role.main.Role(
            name="test2", realname="test_role", perm=["app://2"],
            role=[role1])
        role2.save()
        role3 = core4.api.v1.role.main.Role(
            name="test3", realname="test_role", perm=["app://3"],
            role=[role2])
        role3.save()
        self.assertEqual(role3._casc_perm, ["app://1", "app://2", "app://3"])
        role3.role = [role1]
        self.assertEqual(role3._casc_perm, ["app://1", "app://3"])
        role3.save()
        test = core4.api.v1.role.main.Role().load_one(name="test3")
        self.assertEqual(test._casc_perm, ["app://1", "app://3"])


if __name__ == '__main__':
    unittest.main()
