import core4.base


class Test(core4.base.CoreBase):
    pass


if __name__ == '__main__':
    b = core4.base.CoreBase()
    t = Test()
    print(b.qual_name(), t.qual_name())
