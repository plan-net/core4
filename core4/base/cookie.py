import core4.base.main


class Cookie(core4.main.Base):

    section = "job"

    def __init__(self, name=None):
        super().__init__()
        settings = self.config.get_collection('sys.cookie', 'job')
        self.cookie_collection = core4.main.CoreCollection(settings)
        self.name = name

    def get(self):
        pass

    def set(self):
        pass

    def inc(self):
        pass

    def dec(self):
        pass

