"""
"""

from datetime import timedelta

import core4.base
import core4.error
import core4.queue.job
import core4.queue.main
import core4.service.setup
import core4.util


class CoreDaemon(core4.base.CoreBase):

    def __init__(self, steps, name=None):
        super().__init__()
        self.identifier = name or core4.util.get_hostname()
        self.hostname = core4.util.get_hostname()
        self.phase = {
            "startup": core4.util.now(),
            "loop": None,
            "shutdown": None,
            "exit": None
        }
        self.plan = None
        self.exit = False
        self.at = None
        self.steps = steps
        self.cycle = dict([(s, 0) for s in steps])
        self.cycle["total"] = 0
        self.queue = core4.queue.main.CoreQueue()

    def start(self):
        """
        executes the daemon's workflow from :meth:`.startup` to the main
        processing :meth:`.loop` to :meth:`.shutdown`.
        :return:
        """
        try:
            self.startup()
            self.loop()
        except KeyboardInterrupt:
            raise SystemExit()
        except:
            raise
        finally:
            self.shutdown()
            self.enter_phase("exit")

    def startup(self):
        """
        Implements the **startup** phase of the daemon.
        """
        self.register()
        self.enter_phase("startup")
        self.create_env()
        self.cleanup()
        self.plan = self.create_plan()

    def register(self):
        """
        Registers the daemon identified by it's ``.identifier`` in collection
        ``sys.worker``.

        .. warning:: please note that the ``.identifier`` of the worker must
                     not exist.
        """
        self.config.sys.worker.update_one(
            {"_id": self.identifier},
            update={
                "$set": {
                    "phase": {},
                    "heartbeat": None,
                    "project": None
                }
            },
            upsert=True
        )
        self.logger.info("registered worker")

    def shutdown(self):
        """
        Shutdown the worker by spawning the final housekeeping
        method :meth:`cleanup`.
        """
        self.enter_phase("shutdown")
        self.cleanup()

    def create_env(self):
        """
        Ensures proper environment setup with required folders and roles.
        This method utilises :class:`core4.service.setup.CoreSetup`. Finally
        this method collects core4 meta information on jobs and pushes the data
        into ``sys.worker``.
        """
        setup = core4.service.setup.CoreSetup()
        setup.make_folder()
        setup.make_role()  # todo: implement!
        setup.make_stdout()
        self.config.sys.worker.update_one(
            {"_id": self.identifier},
            update={
                "$set": {
                    "project": setup.collect_jobs()
                }
            }
        )
        self.logger.info("registered worker")

    def cleanup(self):
        """
        General housekeeping method of the worker.
        :return:
        """
        pass

    def create_plan(self):
        """
        Creates the worker's execution plan in the main processing loop:

        # :meth:`.work_jobs` - get next job, inactivate or execute
        # :meth:`.remove_jobs` - remove jobs
        # :meth:`.flag_jobs` - flag jobs as non-stoppers, zombies, killed
        # :meth:`.collect_stats` - collect and save general sever metrics

        :return: dict with step ``name``, ``interval``, ``next`` timestamp
                 to execute and method reference ``call``
        """
        plan = []
        now = core4.util.now()
        self.wait_time = None
        for s in self.steps:
            interval = self.config.worker.execution_plan[s]
            if self.wait_time is None:
                self.wait_time = interval
            else:
                self.wait_time = min(interval, self.wait_time)
            self.logger.debug("set [%s] interval [%1.2f] sec.", s, interval)
            plan.append({
                "name": s,
                "interval": interval,
                "next": now + timedelta(seconds=interval),
                "call": getattr(self, s)
            })
        self.logger.debug(
            "create execution plan with cycle time [%1.2f] sec.",
            self.wait_time)
        return plan

    def enter_phase(self, phase):
        """
        This method advertises current execution phase in collection
        ``sys.worker``.

        :param phase: current phase
        """
        self.phase[phase] = core4.util.mongo_now()
        ret = self.config.sys.worker.update_one(
            {"_id": self.identifier},
            update={
                "$set": {
                    "phase.{}".format(phase): self.phase[phase]
                }
            }
        )
        if ret.raw_result["n"] == 1:
            self.logger.info("enter phase [%s]", phase)
        else:
            raise core4.error.Core4SetupError(
                "failed to enter phase [{}]".format(phase))

    def loop(self):
        """
        This is the main processing phase of the worker entered by
        :meth:`.start`. This method skips processing if core4 system is in the
        general *maintenance* state indicated in collection ``sys.worker``.

        The loop is left if core4 system is in the general *__halt__* state as
        indicated in collection ``sys.worker``, too.
        """
        raise NotImplementedError
