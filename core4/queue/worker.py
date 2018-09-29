
import core4.base
import core4.util
import datetime
import time
import core4.service.setup


class CoreWorker(core4.base.CoreBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.plan = None
        self.exit = False
        self.at = None
        self.cycle_no = 0

    def start(self):
        self.enter_phase("startup")
        self.create_worker_env()
        self.register_worker()
        self.register_projects()
        self.cleanup()
        self.plan = self.create_plan()
        self.loop()
        self.shutdown()

    def create_worker_env(self):
        setup = core4.service.setup.CoreSetup()
        setup.make_folder()
        setup.make_role()
        self.create_stats()

    def create_dirs(self):
        pass

    def create_stats(self):
        pass

    def create_roles(self):
        pass

    def register_worker(self):
        pass

    def register_projects(self):
        pass

    def cleanup(self):
        pass

    def create_plan(self):
        steps = (
            "work_jobs",
            "kill_jobs",
            "inactive_jobs",
            "nonstop_jobs",
            "nopid_jobs",
            "collect_stats")
        plan = []
        now = core4.util.now()
        self.wait_time = None
        for s in steps:
            interval = self.config.worker.execution_plan[s]
            if self.wait_time is None:
                self.wait_time = interval
            else:
                self.wait_time = min(interval, self.wait_time)
            self.logger.debug("set [%s] interval [%1.2f] seconds",
                              s, interval)
            plan.append({
                "name": s,
                "interval": interval,
                "next": now + datetime.timedelta(seconds=interval),
                "call": getattr(self, s)
            })
        return plan

    def enter_phase(self, phase):
        self.logger.info("enter phase [%s]", phase)

    def loop(self):
        self.enter_phase("loop")
        while not self.exit:
            self.cycle_no += 1
            # create some idle time
            time.sleep(self.wait_time)
            self.at = core4.util.now()
            for step in self.plan:
                interval = datetime.timedelta(seconds=step["interval"])
                if step["next"] <= self.at:
                    self.logger.debug("enter [%s] at cycle [%s]",
                                      step["name"], self.cycle_no)
                    step["call"]()
                    self.logger.debug("exit [%s] at cycle [%s]",
                                      step["name"], self.cycle_no)
                    step["next"] = self.at + interval

    def work_jobs(self):
        pass

    def kill_jobs(self):
        pass

    def inactive_jobs(self):
        pass

    def nonstop_jobs(self):
        pass

    def nopid_jobs(self):
        pass

    def collect_stats(self):
        pass

    def shutdown(self):
        self.enter_phase("shutdown")

    def execute(self):
        pass

    def save_job(self):
        pass

    def load_job(self):
        pass