import hashlib
import json
import sys

import datetime as dt

import core4.base.cookie
import core4.error
import core4.util
import core4.util.node
from core4.base.main import CoreBase
from core4.queue.validate import *

# Job-States
STATE_PENDING = 'pending'
STATE_RUNNING = 'running'
STATE_COMPLETE = 'complete'
STATE_DEFERRED = 'deferred'
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
    "_hash": (SERIALISE,),
    "args": (ENQUEUE, SERIALISE,),
    "attempts": (ENQUEUE, CONFIG, PROPERTY, SERIALISE,),
    "attempts_left": (SERIALISE,),
    "author": (PROPERTY,),
    "chain": (ENQUEUE, CONFIG, PROPERTY, SERIALISE,),
    "defer_max": (ENQUEUE, CONFIG, PROPERTY, SERIALISE),
    "defer_time": (ENQUEUE, CONFIG, PROPERTY, SERIALISE,),
    "dependency": (ENQUEUE, CONFIG, PROPERTY, SERIALISE,),
    "enqueued": (SERIALISE,),
    "error_time": (ENQUEUE, CONFIG, PROPERTY, SERIALISE,),
    "finished_at": (SERIALISE,),
    "force": (ENQUEUE, CONFIG, PROPERTY, SERIALISE,),
    "hidden": (CONFIG, PROPERTY,),
    "inactive_at": (SERIALISE,),
    "killed_at": (SERIALISE,),
    "last_error": (SERIALISE,),
    "locked": (SERIALISE,),
    "max_parallel": (ENQUEUE, CONFIG, PROPERTY, SERIALISE,),
    "name": (SERIALISE,),
    "priority": (ENQUEUE, CONFIG, PROPERTY, SERIALISE,),
    "progress_interval": (ENQUEUE, CONFIG, PROPERTY, SERIALISE,),
    "python": (ENQUEUE, CONFIG, PROPERTY, SERIALISE,),
    "query_at": (SERIALISE,),
    "removed_at": (SERIALISE,),
    "runtime": (SERIALISE,),
    "schedule": (CONFIG, PROPERTY,),
    "sources": (SERIALISE,),
    "started_at": (SERIALISE,),
    "state": (SERIALISE,),
    "tag": (CONFIG, PROPERTY,),
    "trial": (SERIALISE,),
    "wall_at": (SERIALISE,),
    "wall_time": (ENQUEUE, CONFIG, PROPERTY, SERIALISE,),
    "worker": (ENQUEUE, CONFIG, PROPERTY, SERIALISE,),
    "zombie_at": (SERIALISE,),
    "zombie_time": (ENQUEUE, CONFIG, PROPERTY, SERIALISE,),
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
    "_id": is_objectid,
    "attempts": is_int_gt0,
    "author": is_str,
    "chain": is_job,
    "defer_max": is_int_gt0,
    "defer_time": is_int_gt0,
    "dependency": is_job,
    "error_time": is_int_gt0,
    "force": is_bool_null,
    "hidden": is_bool_null,
    "max_parallel": is_int_gt0_null,
    "priority": is_int,
    "progress_interval": is_int_gt0,
    "schedule": is_cron,
    "tag": is_str_list_null,
    "wall_time": is_int_gt0_null,
    "worker": is_str_null,
    "zombie_time": is_int_gt0,
}

# job properties not inherited from parent class
NOT_INHERITED = {
    "schedule": None,
    "dependency": [],
    "chain": []
}


class CoreJob(CoreBase):
    """
    This is the base class of all core jobss. Core jobs implement the actual
    task processing. If you say that :class:`.Worker` is the working horse of
    core, then jobs tell these workers *what* to do.

    To control these activities in a distributed job execution environment,
    jobs have several properties. Some are read only attributes. Other can be
    specified by the developer and core operator in multiple ways (see below).

    The following table describes all job properties in alphabetical order.

    .. _job_attributes:

    * ``_id`` - job identifier in ``sys.queue``
    * ``args`` - arguments passed to the job
    * ``attempts`` - maximum number of execution attempts after job failure
      before the job enters the final ``error`` state
    * ``attempts_left`` -  number of attempts left after failure
    * ``author`` - the author(s) of the job
    * ``defer_max`` - maximum number of seconds to defer the job before the job
      turns inactive
    * ``defer_time`` - seconds to wait before restart after defer
    * ``dependency`` - list of jobs which need complete before execution
    * ``chain`` - list of jobs to be enqueued after successful job completion
    * ``enqueued`` - dict with information about job enqueuing
    * ``enqueued.at`` - datetime when the job has been enqueued
    * ``enqueued.hostname`` - from where the job has been enqueued
    * ``enqueued.parent_id`` - job id of the precursing job which has been
      journaled and restarted
    * ``enqueued.child_id`` - job id of the follow-up job which has been
      launched
    * ``enqueued.username`` - user who enqueued the job
    * ``error_time`` - seconds to wait before job restart after failure
    * ``finished_at`` - datetime when the job finished with success, failure,
      or deferral
    * ``force`` - if ``True`` then ignore worker resource limits and launch
      the job
    * ``hidden`` - if ``True`` then hide the job from job listing (defaults to
      ``False``)
    * ``inactive_at`` - datetime  when a deferring job turns inactive, derived
      from ``defer_max``
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
    * ``name`` - short fully qualified name of the job
    * ``priority`` - to execute the job with >0 higher and <0 lower priority
    * ``python`` - Python executable to be used for dedicated Python virtual
      environment
    * ``query_at`` - datetime to query the job, derived from ``error_time`` or
      ``defer_time``
    * ``removed_at`` - datetime when the job has been requested to remove
    * ``runtime`` - total job execution time
    * ``schedule`` - job schedule in crontab format
    * ``sources`` - set of sources processed by the job
    * ``started_at`` - last job execution start-time
    * ``state`` - job state
    * ``tag`` - tag the job with freestyle string-argmuents
    * ``wall_at`` - datetime when a running job turns into a non-stopping job,
      determined by ``wall_time``
    * ``wall_time`` - number of seconds before a running job turns into a
      non-stopping job
    * ``worker`` - eligable to execute the job
    * ``zombie_at`` - datetime when the job not advertising any progress is
      flagged a zombie
    * ``zombie_time`` - number of seconds before a job turns into a zombie
      non-stopping job

    **job property definition scheme**

    Job properties can be specified in the following three ways,
    if a property is defined within more then one definition scheme hinted
    order is applied:

    #. job properties can be defined by parameters passed to
       :meth:`.enqueue <core4.queue.job.CoreJob.enqueue>`
    #. job properties can be defined in configuration settings
    #. job properties can be defined as a class property

    .. warning: these properties cannot be implemented directed with
                ``self.query_at = datetime.datetime.now()`. This throws an
                :class:`.CoreUsageError` exception.

    Note that not all properties support all three definition schemes. The
    following table provides information about which user-defined job
    properties support one or more definition scheme. Furthermore the table
    informs about the default value, applied validation rules and if the
    property is saved into ``sys.queue``.

 ================= ======= ====== ===== ========= ======= ====================
          property enqueue config class serialise default validation
 ================= ======= ====== ===== ========= ======= ====================
               _id   False  False False      True      na
              args    True  False False      True      na
          attempts    True   True  True      True       1 int > 0
     attempts_left   False  False False      True      na
            author   False  False  True     False      na str
             chain    True   True  True      True    ([]) list of jobs, None
         defer_max    True   True  True      True     60' int > 0
        defer_time    True   True  True      True      5' int > 0
        dependency    True   True  True      True    ([]) list of jobs, None
          enqueued   False  False False      True      na
        error_time    True   True  True      True     10' int > 0
       finished_at   False  False False      True      na
             force    True   True  True      True   False is bool
            hidden   False   True  True     False   False is bool
       inactive_at   False  False False      True      na
         killed_at   False  False False      True      na
        last_error   False  False False      True      na
            locked   False  False False      True      na
      max_parallel    True   True  True      True    None int > 0, None
          priority    True   True  True      True       0 int
           python     True   True  True      True  note-1 os.path.exist
 progress_interval    True   True  True      True       5 int > 0
              name   False  False False      True      na
          query_at   False  False False      True      na
        removed_at   False  False False      True      na
           runtime   False  False False      True      na
          schedule   False   True  True     False    None crontab format, None
           sources   False  False False      True      na
        started_at   False  False False      True      na
             state   False  False False      True      na
               tag   False   True  True     False    ([]) list of str, None
           wall_at   False  False False      True      na
         wall_time    True   True  True      True    None int > 0, None
            worker    True   True  True      True    ([]) list of str, None
         zombie_at   False  False False      True      na
       zombie_time    True   True  True      True    1800 int > 0
 ================= ======= ====== ===== ========= ======= ====================

    .. note:: **note-1**: The default value for ``python`` is defined by the
              {{DEFAULT.python}} variable.


    Best practice is to put the section definitions as class variables. Define
    all other property settings into the configuration section of the job. The
    job configuration must be located in the extra configuration file of the
    project package.


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

    Additionally to the job state property there are four flags indicating
    special job management:

    * **zombie** - if not *None* indicates that the job is considered a zombie
      job
    * **nonstop** - if not *None* indicates that the job is considered a
      non-stopping job
    * **removed** - if not *None* indicates a request to remove the job from
      ``sys.queue``
    * **killed** - if not *None* indicates that the job has been killed

    .. note:: There might be even cases, where you might want to hide a job
              from for these jobs. any job listing. Set the ``hidden`` class
              variable to *True*

    **job schedules**

    The preferred job execution automation mechanic uses ``sys.queue``. Using
    core's queue brings the advantage of load balances onto the table.

    The schedule defines the time interval using crontab format to trigger job
    execution. Duplicate parameterised jobs are not allowed.

    """
    author = None
    attempts = None
    chain = None
    dependency = None
    priority = None
    tag = None
    worker = None
    defer_time = None
    defer_max = None
    error_time = None
    force = None
    hidden = None
    wall_time = None
    max_parallel = None
    schedule = None
    progress_interval = None
    zombie_time = None

    _frozen_ = False

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
        self._hash = None
        self._cookie = None
        self.args = {}
        self.attempts_left = None
        self.enqueued = None
        self.finished_at = None
        self.inactive_at = None
        self.killed_at = None
        self.last_error = None
        self.locked = None
        self.query_at = None
        self.removed_at = None
        self.runtime = None
        self.sources = None
        self.started_at = None
        self.state = None
        self.trial = 0
        self.wall_at = None
        self.zombie_at = None

        self.load_default()
        self.overload_property()
        self.overload_config()
        self.overload_args(**kwargs)

        if self.args:
            js = json.dumps(self.args, sort_keys=True)
            self._hash = hashlib.md5(js.encode("utf-8")).hexdigest()

        self.identifier = self._id
        self._frozen_ = True

    def __setattr__(self, key, value):
        """
        Setting an class-attribute is only allowed if ``_frozen`` is ``False``.
        The ``_frozen`` attribute is automatically set to ``True`` after object
        instantiation.
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

        :raises: ``AssertionError`` if no author is set or asserts if attribute
                 is not of its intended type.
        """
        for prop, check in JOB_VALIDATION.items():
            check(prop, getattr(self, prop))
        # special handling of author property
        if "author" not in self.__class__.__dict__:
            raise AssertionError("missing author in [{}]".format(
                self.qual_name()))

    def load_default(self):
        """
        sets the default class-attributes given in the job-section of the
        config.
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

    def overload_property(self):
        """
        sets all job-attributes that can be found within the config.
        """
        for prop in PROPERTY_ARGS:
            if prop in self.__class__.__dict__:
                setattr(self, prop, self.__class__.__dict__[prop])

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

        :return: :class:`.Cookie`
        """
        if not self._cookie:
            self._cookie = core4.base.cookie.Cookie(
                self.qual_name(short=True), self.config.sys.cookie)
        return self._cookie

    def progress(self, p, *args, force=False):
        """
        monitors the progress of a job. This method is called on the set
        intervall.

        This method pdates the job's heartbeat and logs the progress with
        a debug messages. If a job does not report progress within a specified
        timeframe, it turns into a zombie.

        :param p: percentage in decimal.
        :param args: message and or format, will be passed to
               :meth:`core4.base.main.CoreBase.format_args`.
        :param force: force progress update, ignoring ``._progress``
        """
        now = core4.util.node.now()

        if (force or self._progress is None or now > self._progress):
            message = self.format_args(*args)
            self.__dict__['_progress'] = now + dt.timedelta(
                seconds=self.progress_interval)
            self.logger.debug("progress [%1.0f%%] - " + message, p * 100.)
            self.config.sys.queue.update_one(
                {
                    "_id": self._id
                },
                update={
                    '$set': {
                        'locked.heartbeat': now,
                        'locked.progress': message,
                        'locked.progress_value': p
                    }
                }
            )

    def defer(self, *args):
        """
        defer the job, this will result in the job being returned to the queue
        and be queried again after ``defer_time``

        :param message: defer message
        :raises: :class:`.CoreJobDefered`
        """
        message = self.format_args(*args)
        raise core4.error.CoreJobDeferred(message)

    def serialise(self):
        """
        Convert the job properties into a dict.

        :return: dict
        """
        doc = dict([(k, self.__dict__[k]) for k in SERIALISE_ARGS])
        if self._id is None:
            del doc["_id"]
        return doc

    @classmethod
    def deserialise(cls, **kwargs):
        """
        This class method converts the passed {{**kwargs**}} keys-/values into
        a job object and :meth:`.validate` and return the object.

        :param kwargs: keys-/values
        :return: :class:`.CoreJob`
        """
        obj = cls()
        for k in kwargs:
            if k in obj.__dict__:
                obj.__dict__[k] = kwargs[k]
        obj.identifier = obj._id
        obj.validate()
        return obj

    def execute(self, **kwargs):
        """
        This method has to be implented by the job developer.
        It is the entry-point of the framework. Code specified in this method
        is executed within the core-ecosystem.

        :param kwargs: passed enqueueing job arguments
        """
        raise NotImplementedError

    def find_executable(self):
        """
        This method is used to find the Python executable/virtual environment
        for the passed job.

        The Python executable is defined by a configuration key named
        ``python`` . If the value is ``None``, then the executable running the
        :class:`.CoreWorker` is used. If configuration variable
        ``worker.virtual_environment_home`` is defined, then the actual
        Python interpreter path is built from this path and the value of the
        ``python`` key. If key ``worker.virtual_environment_home`` is ``None``,
        then the ``python`` key must address the full path to the Python
        interpreter.

        :param job: :class:`.CoreJob` object
        :return: full path (str) to Python executable
        """
        if self.python:
            if self.config.worker.virtual_environment_home:
                executable = os.path.join(
                    self.config.worker.virtual_environment_home, self.python)
            else:
                executable = self.python
        else:
            executable = sys.executable
        if not os.path.exists(executable):
            raise FileNotFoundError(
                "Python executable [{}] not found for [{}]".format(
                    executable, self.qual_name()
                ))
        return executable


