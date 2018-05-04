
class Base():

    def __init__(self):
        self.account = None
        self.config = self._init_config()
        self.logger = self._init_logging()
        self.section = self.account or 'DEFAULT'
        pass

    def _init_logging(self):
        pass

    def _init_config(self):
        pass

    def qual_name(self):
        pass

    def identifier(self):
        pass


