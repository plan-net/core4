# -*- coding: utf-8 -*-

import os
import unittest
import sys
import core4.base
#import core4.logger

os.environ["CORE4_OPTION_mongo_url"] = "mongodb://core:654321@localhost:27017"


class TestBase(unittest.TestCase):

    # def test_something(self):
    #     import time
    #     time.sleep(1)
    #     self.assertEqual(True, True)

    def test_base(self):
        b = core4.base.CoreBase()
        self.assertEqual("core4.base.main.CoreBase", b.qual_name())
        self.assertEqual("core4.base.main.CoreBase", b.qual_name(short=False))

    def test_plugin(self):
        import plugin.test
        t = plugin.test.Test()
        self.assertEqual("plugin", t.account)
        #self.assertEqual("plugin", t.section)
        self.assertEqual("plugin.test.Test", t.qual_name())
        self.assertEqual("core4.account.plugin.test.Test", t.qual_name(
            short=False))
        self.assertEqual("plugin.test.Test()", "{}".format(t))
        t = plugin.test.Test()
        self.assertEqual("plugin.test.Test()", repr(t))


    def test_binding(self):
        pass

    def _test_binding(self):

        class A(core4.base.CoreBase):

            def ok(s):
                return "OK A"

        class B(A):

            def ok(s):
                s.a = A()
                return "OK B - " + s.a.ok()

        b = B()
        self.assertEqual("OK B - OK A", b.ok())
        #self.assertNotEqual(b.identifier, b.a.identifier)

        class C(core4.base.CoreBase):

            def ok(s):
                return "OK C"

        class D(C):

            def ok(s):
                s.identifier = "123"
                #s.c = s.bind(C())
                s.c = C()
                return "OK D - " + s.c.ok()

            # def extend(s):
            #     s.e = C(bind=s)

        d = D()
        self.assertEqual("OK D - OK C", d.ok())
        #self.assertEqual(d.identifier, d.c.identifier)
        #d.extend()
        #self.assertEqual(d.e.identifier, d.identifier)

    def test_plugin_conf(self):
        import plugin.test
        t = plugin.test.Test()
        self.assertTrue(t.account_conf().endswith("core4/plugin/plugin.py"))
        self.assertEqual(t.config.mongo_database, "core4test")
        self.assertEqual(repr(t), "plugin.test.Test()")
        #print(t.config)
        test = eval(repr(t.config))
        self.assertEqual(test, t.config)

    def test_main(self):
        import plugin.test
        from subprocess import check_output
        pp = os.path.dirname(core4.__file__) + "/.."
        environ = os.environ
        os.environ["PYTHONPATH"] = pp
        out = check_output([sys.executable, plugin.test.__file__], env=environ)
        self.assertEqual(out.decode("utf-8").strip(),
                         'core4.base.main.CoreBase plugin.test.Test')


if __name__ == '__main__':
    unittest.main()
