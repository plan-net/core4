# -*- coding: utf-8 -*-

import core4.base


class Controller(core4.base.CoreBase):

    def execute(self):
        self.identifier = "0815"
        self.logger.info("starting")
        slave = Slave1()
        slave.process()
        self.logger.info("ending")


class Slave1(core4.base.CoreBase):

    def process(self):
        self.logger.info("starting")
        subslave1 = Slave2()
        subslave1.process()
        b = core4.base.CoreBase()
        b.logger.info("hello from core4")
        self.logger.info("ending")


class Slave2(core4.base.CoreBase):

    def process(self):
        self.logger.info("starting")
        self.logger.info("ending")


class Massive(core4.base.CoreBase):

    def execute(self):
        self.logger.warning("start preps")
        data = []
        for i in range(100):
            data.append(Controller())
        self.logger.warning("done preps, start execution")
        for d in data:
            d.execute()
