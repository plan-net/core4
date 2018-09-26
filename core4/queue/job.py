import core4.error
from core4.base.main import CoreBase
from core4.queue.validate import *
import core4.util
import datetime as dt

# Job-States
STATE_PENDING = 'pending'
STATE_RUNNING = 'running'
STATE_COMPLETE = 'complete'
STATE_DEFERRED = 'deferred'
STATE_SKIPPED = 'skipped'
STATE_FAILED = 'failed'
STATE_INACTIVE = 'inactive'
STATE_ERROR = 'error'
STATE_KILLED = 'killed'

# relevant job property definition schemes
ENQUEUE = 0  # property can be set by enqueuing user
CONFIG = 1  # property can be set in configuration
PROPERTY = 2  # property can be set as a class property
SERIALISE = 3  # property is to be materialised in sys.queue

# job property definition scope
JOB_ARGS = {
    "_id": (SERIALISE,),
    "args": (ENQUEUE, SERIALISE,),
    "attempts": (ENQUEUE, CONFIG, PROPERTY, SERIALISE,),
    "attempts_left": (SERIALISE,),
    "author": (PROPERTY,),
    "chain": (ENQUEUE, CONFIG, PROPERTY, SERIALISE,),
    "defer_max": (ENQUEUE, CONFIG, PROPERTY,),
    "defer_time": (ENQUEUE, CONFIG, PROPERTY, SERIALISE,),
    "dependency": (ENQUEUE, CONFIG, PROPERTY, SERIALISE,),
    "enqueued": (SERIALISE,),
    "error_time": (ENQUEUE, CONFIG, PROPERTY, SERIALISE,),
    "finished_at": (SERIALISE,),
    "force": (ENQUEUE, CONFIG, PROPERTY, SERIALISE,),
    "hidden": (CONFIG, PROPERTY,),
    "inactive_at": (SERIALISE,),
    "inactive_time": (ENQUEUE, CONFIG, PROPERTY, SERIALISE,),
    "killed_at": (SERIALISE,),
    "last_error": (SERIALISE,),
    "locked": (SERIALISE,),
    "max_parallel": (ENQUEUE, CONFIG, PROPERTY, SERIALISE,),
    "name": (SERIALISE,),
    "nodes": (ENQUEUE, CONFIG, PROPERTY, SERIALISE,),
    "nonstop_at": (SERIALISE, 9),
    "priority": (ENQUEUE, CONFIG, PROPERTY, SERIALISE,),
    "query_at": (SERIALISE,),
    "remove_at": (SERIALISE,),
    "runtime": (SERIALISE,),
    "schedule": (CONFIG, PROPERTY,),
    "sources": (SERIALISE,),
    "started_at": (SERIALISE,),
    "state": (SERIALISE,),
    "tag": (CONFIG, PROPERTY,),
    "wall_at": (SERIALISE,),
    "wall_time": (ENQUEUE, CONFIG, PROPERTY, SERIALISE,),
    "zombie_at": (SERIALISE,),
    "_frozen_": (ENQUEUE,),
    "progress_interval": (ENQUEUE, CONFIG, PROPERTY, SERIALISE,),
}

# property scope to load from config
CONFIG_ARGS = tuple([k for k, v in JOB_ARGS.items() if CONFIG in v])
# property scope to load from class
PROPERTY_ARGS = tuple([k for k, v in JOB_ARGS.items() if PROPERTY in v])
# property scope to set default values
DEFAULT_ARGS = tuple(set(CONFIG_ARGS + PROPERTY_ARGS))
# property scope to parse from enqueue
ENQUEUE_ARGS = tuple([k for k, v in JOB_ARGS.items() if ENQUEUE in v])
# property scope to materialise
SERIALISE_ARGS = tuple([k for k, v in JOB_ARGS.items() if SERIALISE in v])

# validation setting
JOB_VALIDATION = {
    "attempts": is_int_gt0,
    "author": is_str,
    "chain": is_job,
    "defer_max": is_int_gt0,
    "defer_time": is_int_gt0,
    "dependency": is_job,
    "error_time": is_int_gt0,
    "force": is_bool_null,
    "hidden": is_bool_null,
    "inactive_time": is_int_gt0,
    "max_parallel": is_int_gt0_null,
    "nodes": is_str_null,
    "priority": is_int,
    "schedule": is_cron,
    "tag": is_str_list_null,
    "wall_time": is_int_gt0_null,
    "progress_interval": is_int_gt0,
}

# job properties not inherited from parent class
NOT_INHERITED = {
    "schedule": None,
    "dependency": [],
    "chain": []
}


class CoreJob(CoreBase):
    """
    This is the base class of all core jobs. Core jobs implement the actual task
    processing. If you say that :class:`.Worker` is the working horse of core,
    then jobs tell these workers *what* to do.

    To control these activities in a distributed job execution environment, jobs
    have several properties. Some are read only attributes. Other can be
    specified by the developer and core operator in multiple ways (see below).

    The following table describes all job properties in alphabetical order.

    * ``_id`` - job identifier in ``sys.queue``
    * ``args`` - arguments passed to the job
    * ``attempts`` - maximum number of execution attempts after job failure
      before the job enters the final ``error`` state
    * ``attempts_left`` -  number of attempts left after failure
    * ``author`` - the author(s) of the job
    * ``defer_max`` - maximum number of seconds to defer the job before restart
    * ``defer_time`` - seconds to wait before restart after defer
    * ``dependency`` - list of jobs which need complete before execution
    * ``chain`` - list of jobs to be enqueued after successful job completion
    * ``enqueued`` - dict with information about job enqueuing
    * ``enqueued.at`` - datetime when the job has been enqueued
    * ``enqueued.hostname`` - from where the job has been enqueued
    * ``enqueued.parent`` - job id of the precursing job which has been
      journaled and restarted
    * ``enqueued.username`` - user who enqueued the job
    * ``error_time`` - seconds to wait before job restart after failure
    * ``finished_at`` - datetime when the job finished with success, failure,
      or deferral
    * ``force`` - if ``True`` then ignore nodes' resource limits and launch the
      job
    * ``hidden`` - if ``True`` then hide the job from job listing (defaults to
      ``False``)
    * ``inactive_at`` - datetime  when a deferring job turns inactive, derived
      from ``defer_max``
    * ``inactive_time`` - seconds before a job which is not advertising the
      progress turns into a zombie
    * ``killed_at`` - datetime when the job has been requested to kill
    * ``last_error`` - last stack trace in case of failure or error
    * ``locked`` - dict with information about the worker
    * ``locked.at`` - datetime when the job has been locked
    * ``locked.heartbeat`` - datetime of the last advertising of job progress
    * ``locked.hostname`` - of the worker
    * ``locked.pid`` - of the process executing the job
    * ``locked.progress`` - last progress message
    * ``locked.worker`` - which locked the job
    * ``locked.username`` - running the worker which locked the job
    * ``max_parallel`` - max. number jobs to run in parallel on the same node
    * ``nodes`` - nodes eligable to execute the job
    * ``nonstop_at`` - datetime when the job turned into a non-stopping job,
      determined by ``wall_time``
    * ``priority`` - to execute the job with >0 higher and <0 lower priority
    * ``name`` - short fully qualified name of the job
    * ``query_at`` - datetime to query the job, derived from ``error_time`` or
      ``defer_time``
    * ``removed_at`` - datetime when the job has been requested to remove
    * ``runtime`` - total job execution time
    * ``schedule`` - job schedule in crontab format
    * ``sources`` - set of sources processed by the job
    * ``started_at`` - last job execution start-time
    * ``state`` - job state
    * ``tag`` - tag the job with freestyle string-argmuents
    * ``wall_at`` - datetime when a running job turns into a non-stopping job
    * ``wall_time`` - number of seconds before a running job turns into a
      non-stopping job
    * ``zombie_at`` - datetime when the job turned into a zombie due to
      lacking progress

    **job property definition schemes**

    Job properties can be specified in three ways:

    #. job properties can be defined by parameters passed to :meth:`.enqueue()`
    #. job properties can be defined in configuration settings
    #. job properties can be defined as a class property

    Note that not all properties support all three definition schemes. The
    following table provides information about which user-defined job properties
    support one or more definition scheme.

    .. note:: if a job property is defined with more than one definition scheme,
              the following order/priority is applied: 1) parameters to
              :meth:`.enqueue()`, 2) key/values in the job configuration,
              3) values specified as class properties.

    ============== ======= ====== ===== ========= ======= ====================
          property enqueue config class serialise default validation
    ============== ======= ====== ===== ========= ======= ====================
               _id   False  False False      True      na
              args    True  False False      True      na
          attempts    True   True  True      True       1 int > 0
     attempts_left   False  False False      True      na
            author   False  False  True     False      na str
             chain    True   True  True      True    ([]) list of jobs, None
         defer_max    True   True  True     False     60' int > 0
        defer_time    True   True  True      True      5' int > 0
        dependency    True   True  True      True    ([]) list of jobs, None
          enqueued   False  False False      True      na
        error_time    True   True  True      True     10' int > 0
       finished_at   False  False False      True      na
             force    True   True  True      True   False is bool
            hidden   False   True  True     False   False is bool
       inactive_at   False  False False      True      na
     inactive_time    True   True  True      True     30' int > 0
         killed_at   False  False False      True      na
        last_error   False  False False      True      na
            locked   False  False False      True      na
      max_parallel    True   True  True      True    None int > 0, None
             nodes    True   True  True      True    ([]) list of str, None
        nonstop_at   False  False False      True      na
          priority    True   True  True      True       0 int
_progress_interval    True   True  True     False       5 int > 0
              name   False  False False      True      na
          query_at   False  False False      True      na
         remove_at   False  False False      True      na
           runtime   False  False False      True      na
          schedule   False   True  True     False    None crontab format, None
           sources   False  False False      True      na
        started_at   False  False False      True      na
             state   False  False False      True      na
               tag   False   True  True     False    ([]) list of str, None
           wall_at   False  False False      True      na
         wall_time    True   True  True      True    None int > 0, None
         zombie_at   False  False False      True      na
    ============== ======= ====== ===== ========= ======= ====================


    Best practice is to put the section definitions as class variables. Define
    all other property settings into the configuration section of the job. The
    job configuration should be located in the extra configuration file of the
    plugin package.


    **job life-cycle**

    We distinguish the following job states:

    * **pending** - ready for execution
    * **running** - in processing by a worker
    * **deferred** - the job has deferred it's execution
    * **complete** - the job successfully finished execution
    * **failed** - job execution failed with attempts left
    * **error** - job execution failed with no attempts left
    * **inactive** - the job continuously deferred execution and is considered
                     inactive
    * **killed** - the job has been killed by a user

    The states *complete*, *error*, *inactive* and *killed* are final states.

    The following diagram depicts the job life-cycle in terms of job states::

                          pending
                            |
                            V
        ,---------------> running <------------------------------.
        |                   |                                    |
        |     ,------.------+--------.---------.---------.       |
        |     |      |      |        |         |         |       |
        |     V      V      V        V         V         V       |
        |   error failed inactive complete   killed   deferred   |
        |            |                                   |       |
        |            |                                   |       |
        `-----------´                                    `-------'

    .. todo:: please use draw.io and create a proper chart

    Additionally to the job state property there are four flags indicating
    special job management:

    * **zombie** - if not *None* indicates that the job is considered a zombie
      job
    * **nonstop** - if not *None* indicates that the job is considered a
      non-stopping job
    * **removed** - if not *None* indicates a request to remove the job from
      ``sys.queue``
    * **killed** - if not *None* indicates that the job has been killed

    .. note:: There might be even cases, where you might want to hide a job from
              any job listing. Set the ``__hidden__`` class variable to *True*
              for these jobs.

    **job schedules**

    The preferred job execution automation mechanic uses ``sys.queue``. Using
    core's queue brings the advantage of load balances onto the table.

    The schedule defines the time interval using crontab format to trigger job
    execution. Duplicate parameterised jobs are not allowed.

    """
    author = None
    attempts = None
    chain = []
    dependency = []
    priority = None
    tag = []
    nodes = None
    defer_time = None
    defer_max = None
    error_time = None
    force = None
    hidden = None
    inactive_time = None
    wall_time = None
    max_parallel = None
    schedule = None
    _frozen_ = False
    progress_interval = 5

    def __init__(self, *args, **kwargs):
        # attributes raised from self.class_config.* to self.*
        self.upwind += list(CONFIG_ARGS)
        # reset properties not to be inherited
        for prop, default in NOT_INHERITED.items():
            if prop not in self.__class__.__dict__:
                self.__dict__[prop] = default

        super().__init__()

        # runtime properties
        self.name = self.qual_name(short=True)
        self._id = None
        self._cookie = None
        self.args = {}
        self.attempts_left = None
        self.enqueued = None
        self.finished_at = None
        self.inactive_at = None
        self.killed_at = None
        self.last_error = None
        self.locked = None
        self.nonstop_at = None
        self.query_at = None
        self.remove_at = None
        self.runtime = None
        self.sources = None
        self.started_at = None
        self.state = None
        self.wall_at = None
        self.zombie_at = None


        self.load_default()
        self.overload_config()
        self.overload_args(**kwargs)
        self._frozen_ = True
        self.__mongo_dict = None


    def __setattr__(self, key, value):
        """
        Setting an class-attribute is only allowed if _frozen has not been set.
        """
        if self._frozen_:
            if key in JOB_ARGS:
                raise core4.error.Core4UsageError(
                    "not allowed to set job class/config property [{}]".format(
                        key))
        super().__setattr__(key, value)

    def validate(self):
        """
        check all standard job-attributes to be of their intended type.
        :raises: AssertionError if no author is set or asserts if attribute is not of its intended type.
        """
        for prop, check in JOB_VALIDATION.items():
            check(prop, getattr(self, prop))
        # special handling of author property
        if "author" not in self.__class__.__dict__:
            raise AssertionError("missing author in [{}]".format(
                self.qual_name()))

    def load_default(self):
        """
        sets the default class-attributes given in the job-section of the config.
        """
        for prop in DEFAULT_ARGS:
            val = getattr(self, prop, None)
            if val is None and prop in self.config.job:
                setattr(self, prop, self.config.job[prop])

    def overload_config(self):
        """
        sets all job-attributes that can be found within the config.
        """
        for prop in CONFIG_ARGS:
            if prop in self.class_config:
                if self.class_config[prop] is not None:
                    setattr(self, prop, self.class_config[prop])

    def overload_args(self, **kwargs):
        """
        sets job-attributes depending on the enqueueing arguments.
        :param kwargs: arguments given by the user while enqueueing.
        """
        for prop, value in kwargs.items():
            if prop in ENQUEUE_ARGS:
                setattr(self, prop, value)
            else:
                self.args[prop] = value

    @property
    def cookie(self):
        """
        cookie of the job depending on its qual_name.
        :return: cookie-instance
        """
        if not self._cookie:
            self._cookie = core4.base.cookie.Cookie(self.qual_name(short=True), self.config.sys.cookie)
        return self._cookie

    def progress(self, p, *args):
        """
        monitor the progress of a job.
        this method is called on a set intervall.
        if a job does not report progress within a specified timeframe, it turns into a zombie.
        updates the jobs heartbeat and logs the progress with debug-messages.
        """
        # Check tuple to have the correct format (float, string)
        if args:
            args = list(args)
            message = args.pop(0)
        else:
            message = ""

        now = core4.util.now()
        if (self._last_progress is None
            # check own document within sys.queue and check for hostname and pid
                or (now >= self._last_progress + dt.timedelta(seconds=self.progress_interval)
                and self.locked and self.locked['host'] == core4.util.get_hostname()
                and self.locked['user'] == core4.util.get_username()
                # pid is not currently included in sys.queue-doc
                and self.locked['pid'] == core4.util.get_pid())):
            if args:
                message = message % tuple(args)
            self.__dict__['_last_progress'] = now
            self.logger.debug(message)
            return self.config.sys.queue.update_one({"_id": self._id}, update={
                '$set': {'locked.heartbeat': core4.util.now(),
                         'locked.progress': message,
                         'locked.progress_value': p}
            })

        # todo: implement
        # this method creates a DEBUG message and updates the heartbeat
        # each progress interval.
        # ensure the hostname + pid is really the owner of the job (mongo filter)


        pass

    def run(self, *args, **kwargs):
        """
        set the nessecary cookie-information on startup and finish of the job.
        log a first progress and call the execute-method of the job.
        """
        # todo: implement
        # the job sets and updates the following attributes
        # - .started_at, finished_at, runtime, last_error
        # note: runtime is the incremental sum (in case of failure and defer)
        #       test this!
        # the method should start and finish with a .progress
        # the method catches all exceptions


        # log entry
        self.progress(0.0, "starting job: {} with id: {}".format(self.qual_name(), self._id))
        try:
            self.__dict__['started_at'] = core4.util.now()
            self.execute(*args, **kwargs)
        except:
            self.__dict__['last_error'] = core4.util.now()
            raise
        finally:
            self.__dict__['finished_at'] = core4.util.now()
            runtime = (self.finished_at - self.started_at).total_seconds()
            if self.runtime is not None:
                runtime += self.runtime
            self.__dict__['runtime'] = runtime
            # is last runtime the finished-time or the starting-time?
            # self.cookie.set("last_runtime", self.finished_at)
            # direct insert here to ignore if last update < 5s
            self.cookie.set("last_runtime", self.finished_at)
            self.config.sys.queue.update_one({"_id": self._id}, update={
                '$set': {'locked.heartbeat': core4.util.now(),
                         'locked.progress': "execution end marker",
                         'locked.progress_value': 1.0,
                         'locked.runtime': self.runtime}
                })

    def defer(self, message=None):
        """
        :param message: error-message
        :raises: CoreJobDefered
        """
        raise core4.error.CoreJobDeferred(message)

    def execute(self, *args, **kwargs):
        """
        this method has to be implented by the user.
        it is the entry-point of the framework.
        code specified in this method is executed within the core-ecosystem.
        :param args: passed argmuents
        :param kwargs: passed enqueueing arguments
        """
        raise NotImplementedError

    @property
    def _mongo_dict(self):
        """
        find your jobs queue-entry.
        :return: mongodb-document representating this job.
        """
        query = {'_id': self._id,
                 'locked.pid': core4.util.get_pid(),
                 'locked.host': core4.util.get_hostname()
                 }

        if not self.__mongo_dict:
            self.__mongo_dict = self.config.sys.queue.find_one(query)
        return self.__mongo_dict

class DummyJob(CoreJob):
    """
    This is just a job-dummy for testing purposes.
    """
    author = 'mra'

# todo: task list


# - test + implement DummyJob.execute
# then:
# - reach 100% test coverage
# - write documentation
# - write job.rst (decide what goes into API docs, and what goes in job.rst)
# - verify sphinx docs format is right and looking good
