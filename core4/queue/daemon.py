import time

import core4.queue.main
import core4.service.introspect
import core4.util
from core4.base.main import CoreBase


class CoreDaemon(CoreBase):
    """
    The daemon class is the base class for :class:`.CoreWorker` and
    :class:`.CoreScheduler`. It delivers the main methods around starting,
    looping and stopping a daemon.

    Each daemon operates in three distinct phases. Each phase features one or
    more processing steps.

    #. **startup** - registers the daemon and available projects, do some
       housekeeping/ cleanup, and several prerequisites, e.g. required
       folders and MongoDB collections are verified
    #. **loop** - the main loop
    #. **shutdown** - again some housekeeping and unregistering the daemon
    #. **exit** - quit daemon

    .. warning:: The daemon ``.identifier`` must be unique.
    """

    def __init__(self, name=None):
        super().__init__()
        self.identifier = name or core4.util.get_hostname()
        self.hostname = core4.util.get_hostname()
        self.phase = {
            "startup": core4.util.now(),
            "loop": None,
            "shutdown": None,
            "exit": None
        }
        self.exit = False
        self.at = None
        self.cycle = {"total": 0}
        self.queue = core4.queue.main.CoreQueue()
        self.jobs = {}
        self.wait_time = None

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
        self.collect_project()

    def cleanup(self):
        """
        General housekeeping method.
        """
        pass

    def register(self):
        """
        Registers the daemon identified by it's ``.identifier`` in collection
        ``sys.worker``.

        .. warning:: please note that the ``.identifier`` of the daemon must
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
        self.logger.info("registered daemon")

    def shutdown(self):
        """
        Shutdown the daemon by spawning the final housekeeping
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
        setup.make_role()
        setup.make_stdout()

    def collect_project(self):
        """
        Inquires existing core4 projects on the node using
        :class:`.CoreIntrospector`. This method stores the identified projects
        alongside some meta information in ``sys.worker``.

        :return:
        """
        intro = core4.service.introspect.CoreIntrospector()
        project = dict([(p["name"], p) for p in intro.iter_project()])
        self.config.sys.worker.update_one(
            {"_id": self.identifier},
            update={
                "$set": {
                    "project": project
                }
            }
        )
        self.logger.info("registered projects")

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
        This is the main processing phase of the daemon entered by
        :meth:`.start`. This method skips processing if core4 system is in the
        general *maintenance* state indicated in collection ``sys.worker``.

        The loop is left if core4 system is in the general *__halt__* state as
        indicated in collection ``sys.worker``, too.
        """
        self.offset = None
        time.sleep(self.wait_time)  # start with cycle 1
        self.enter_phase("loop")
        in_maintenance = False
        while not self.exit:
            self.cycle["total"] += 1
            self.logger.debug("cycle [%d]", self.cycle["total"])
            if self.queue.halt(at=self.phase["startup"]):
                return
            if self.queue.maintenance():
                if not in_maintenance:
                    in_maintenance = True
                    self.logger.info("entering maintenance")
            else:
                if in_maintenance:
                    in_maintenance = False
                    self.logger.info("leaving maintenance")
                self.at = core4.util.now()
                self.run_step()
            time.sleep(self.wait_time)

    def run_step(self):
        """
        This method implements the steps of the daemon. It has to be
        implemented in the class derived from :class:`.CoreDaemon`.
        """
        raise NotImplementedError
