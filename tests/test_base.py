import unittest


class TestRootBase(unittest.TestCase):

    def test_something(self):
        import time
        time.sleep(3)
        self.assertEqual(True, True)


if __name__ == '__main__':
    unittest.main()
