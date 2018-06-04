# -*- coding: utf-8 -*-


class Base:

    def __init__(self):
        self.account = None
        self.config = self._init_config()
        self.logger = self._init_logging()
        self.section = self.account or 'DEFAULT'

    def _init_logging(self):
        return None

    def _init_config(self):
        return None

    def qual_name(self):
        pass

    def identifier(self):
        pass
