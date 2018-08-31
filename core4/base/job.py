from core4.config.main import CoreConfig
from core4.base.main import CoreBase
import core4.base.cookie
import time


STATE_PENDING = 'pending'
STATE_RUNNING = 'running'
STATE_FAILED = 'failed'
STATE_DEFERRED = 'deferred'
STATE_ERROR = 'error'
STATE_COMPLETE = 'complete'
STATE_INACTIVE = 'inactive'
STATE_KILLED = 'killed'

class CoreJob(CoreBase):

    """
    This is the base class of all core jobs. Core jobs implement the actual task
    processing. If you say that :class:`.Worker` is the working horse of core,
    then jobs tell these workers *what* to do.

    In the context of data integration automation jobs

    * download data from providers using various protocols
    * load data into mongo
    * transform data in mongo
    * aggregate data from mongo
    * export data from mongo

    All mongo manipulations use :class:`.CoreJobCollection`.

    **job properties**

    To control these activities in a distributed job execution environment, jobs
    have several properties. Some are read only attributes. Other can be
    specified by the developer and core operator in multiple ways (see below).

    The following table describes all job properties in alphabetical order.

    =================== =============== ===========================================================================
    job property        handle          description
    =================== =============== ===========================================================================
    plugin              auto-assigned   plugin the job is running under
    args                user-defined    arguments passed to the job
    attempts            user-defined    maximum number of execution attempts after job failure
    attempts_left       read-only       number of attempts left after failure
    author              user-defined    the author(s) of the job
    defer_max           user-defined    maximum number of seconds to defer the job
    defer_time          user-defined    seconds to wait before restart after exception JobDeferred
    dependency          user-defined    list of jobs which need to complete before execution starts
    chain               user-defined    list of jobs which are enqueued after a job finishes
    enqueued            read-only       dictionary of information about the job creator
    enqueued.at         read-only       datetime when the job has been enqueued
    enqueued.host       read-only       name of the host from where the job has been enqueued
    enqueued.parent     read-only       job id of the precursing job which has been journaled and restarted
    enqueued.user       read-only       user who enqueued the job
    error_time          user-defined    seconds to wait before restart after job failure
    finished            read-only       datetime when the job finished with success, failure, or deferral
    inactive_at         read-only       datetime  when a deferring job turns inactive, derived from defer_max
    job_id              read-only       job id taken from mongo document _id
    killed              read-only       datetime when the job has been killed
    last_error          read-only       last stack trace in case of failure or error
    locked              read-only       dictionary of information about the job consumer
    locked.at           read-only       datetime when the job has been locked by a worker
    locked.heartbeat    read-only       datetime of the last advertising of job progress
    locked.host         read-only       hostname of the worker which locked the job
    locked.pid          read-only       process id of the worker which locked the job
    locked.progress     read-only       last progress message of the job
    locked.worker       read-only       name of the worker which locked the job
    locked.user         read-only       name of the user running the worker which locked the job
    max_parallel        user-defined    maximum number of this jobs to run in parallel on the same node
    memory              user-defined    mininmum memory requirements in GB
    name                read-only       fully qualified name of the job
    nodes               user-defined    nodes eligable to execute the job
    nonstop             read-only       datetime when the job turned into a non-stopping job, determined by wall_time
    priority            user-defined    priority to execute the job with >0 higher and <0 lower priority
    query_at            read-only       datetime to re-execute the job, derived from error_time or defer_time
    removed             read-only       datetime of the request to remove the job
    runtime             read-only       job execution run-time
    schedule            user-defined    job schedule in crontab format
    section             user-defined    default config section
    sources             read-only       set of sources processed by the job
    started             read-only       job execution start-time
    state               read-only       job state
    wall_at             read-only       datetime when a running job turns into a non-stopping job
    wall_time           user-defined    number of seconds before a running job turns into a non-stopping job
    zombie              read-only       datetime when the job turned into a zombie due to lacking progress
    =================== =============== ===========================================================================

    .. note:: properties *section*, *schedule* and *author* are not saved into
              the job queue (``sys.queue`` and ``sys.journal``).

    **job property definition schemes**

    Job properties can be specified in three ways:

    #. job properties can be defined by parameters passed to :meth:`.enqueue()`
    #. job properties can be defined in core configuration files
    #. job properties can be defined as a class variable

    Note that not all properties support all three definition schemes. The
    following table provides information about which user-defined job properties
    support one or more definition scheme.

    .. note:: if a job property is defined with more than one definition scheme,
              the following order/priority is applied: 1) parameters to
              :meth:`.enqueue()`, 2) options in the job's core configuration
              section, 3) values specified as class variabled.

    ============ ==================== ================== ============== ========================== =====================
    job property :meth:`.enqueue`     core configuration class property default option             default value
    ============ ==================== ================== ============== ========================== =====================
    account      not supported        not supported      not supported  not applicable             automatically set
    args         supported            not supported      not supported  empty dictionary
    attempts     supported            supported          supported      see core.conf, section job 1
    author       not supported        supported          supported      see core.conf, section job None
    defer_max    supported            supported          supported      see core.conf, section job 3600 seconds
    defer_time   supported            supported          supported      see core.conf, section job 360 seconds
    dependency   not supported        supported          supported      see core.conf, section job empty list
    chain        supported            supported          supported      see core.conf, section job empty list
    error_time   supported            supported          supported      see core.conf, section job 3600 seconds
    force        supported            supported          supported      see core.conf, section job False
    memory       supported            supported          supported      see core.conf, section job None
    max_parallel supported            supported          supported      see core.conf, section job None
    nodes        supported            supported          supported      see core.conf, section job empty list (any)
    priority     supported            supported          supported      see core.conf, section job 0 (normal)
    schedule     not supported        supported          supported      see core.conf, section job None
    section      not supported        not supported      supported      None                       DEFAULT
    wall_time    supported            supported          supported      see core.conf, section job None
    ============ ==================== ================== ============== ========================== =====================

    Best practice is to put the section definitions as class variables. Define
    all other property settings into the configuration section of the job. The
    job configuration should be located in the extra configuration file of the
    account package.


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

    .. note:: There are cases, where you might want to use inheritance to define
              general or global job settings in an **abstract job** class and to
              inherit from this abstract job for actual jobs. Set the
              ``__abstract__`` class variable to *True* for these abstract jobs.
              This setting will exclude this abstract job from any job listings.

    .. note:: There might be even cases, where you might want to hide a job from
              any job listing. Set the ``__hidden__`` class variable to *True*
              for these jobs.

    **job schedules**

    The preferred job execution automation mechanic uses ``sys.queue``. Using
    core's queue brings the advantage of load balances onto the table.

    The schedule defines the time interval using crontab format to trigger job
    execution. Duplicate parameterised jobs are not allowed.

    If you need to ensure that a job is running at a pre-defined time, you
    need to prefix the schedule with ``force:`` as in the following example::

        schedule = 'force: 60 * * * *'

    Even though ``coco --cron`` fully supports this feature, the preferred
    execution automation is to use ``sys.queue``.
    """



    def __init__(self, **kwargs):

        """
        Instantiates the job by loading any extra configuration file and
        initialising the job.

        Default variables are documented above in the Job-Class

        :param kwargs: enqueueing-arguments to be passed to the job
        """

        self._cookie = None
        self.author = "mkr"
        self.section = "job"


        # set default vars.
        self.job_args = {}
        self.nodes = None
        self.priority = None
        self.chain = None
        self.tags = []
        self.adhoc = False
        self.defer_max = 36000
        self.defer_time = 600
        self.error_time = 3600
        self.dependency = None
        self.max_parallel = None
        self.wall_at = 0
        self.wall_time = 0

        super().__init__()

        # defaults from the config take preceedence over class-defaults.
        self.load_config()

        # enqueueing arguments take preceedence over config-defaults.
        if kwargs:
            for key, value in kwargs.items():
                if key in self.__dict__.keys() and key is not "config":
                    setattr(self, key, value)
                else:
                    self.job_args[key] = value

        # these vars are written by the queue-only.
        self.equeued = None
        self.enqueued_at = None
        self.enqueued_hostname = None
        self.enqueued_parent = None
        self.enqueued_username = None
        self.error_time = None
        self.attempts_left = None
        self.query_at = None
        self.runtime = None
        self.job_id = None
        self.started = None
        self.finished = None
        self.runtime = None
        self.status = None


    def load_config(self):
        """
        Load all present values in the config and update current values.
        """
        for i in self.config.job:
            n = self.config.job.get(i)
            setattr(self, i, n)

    def serialize(self):
        """
        Serialize a job for manifestating it within the mongo or any other document-store
        :returns dict
        """
        serialize_args = ["job_args","nodes","priority","chain","tags","adhoc","defer_max",
                          "defer_time","error_time","dependency","max_parallel","wall_at","wall_time"]

        tmp = {}

        for i in serialize_args:
            tmp[i] = self.__getattribute__(i)

        return tmp


    def deserialize(self, args={}):
        """
        Deserialize a Job from a given dict.
        Updates a jobs params from a given dict.
        """
        if args:
            for key, value in args.items():
                if key == '_id':
                    key = 'job_id'
                setattr(self, key, value)
        else:
            raise KeyError


    def __eq__(self, obj):
        '''
        compares two Jobs by serializing them and comparing the dicts.
        :param obj: compare Object
        :return: True or False
        '''
        if isinstance(obj, CoreJob):
            ret = self.serialize() == obj.serialize()
        elif isinstance(obj, dict):
            ret = self.serialize() == obj
        else:
            ret = False

        return ret

    def execute(self, *args, **kwargs):
        """
        This is the actual task processing. The method needs to be overwritten
        during job implementations.
        """
        raise NotImplementedError('.execute(*args, **kwargs) needs to be implemented')


    @property
    def cookie(self):
        """
        This is the access layer to the job's cookie. See also :class:`.Cookie`.
        """
        if not self._cookie:
            self._cookie = core4.base.cookie.Cookie(self.qual_name())
        return self._cookie


    def progress(self):
        '''
        Trigger a progress-update from queue/worker
        :return:
        '''
        # trigger update of progress from queue/worker
        pass



class DummyJob(CoreJob):
    """
    This is a simple example job sleeping and reporting progress for the
    specified time in seconds.
    """

    author = 'mra'
    def execute(self, sleep=10):
        time.sleep(10)

#     def execute(self, sleep=1, verbose=False, *args, **kwargs):
#         self.logger.debug('just sleeping for [%s]', sleep)
#         t0 = datetime.datetime.now()
#         t1 = t0 + datetime.timedelta(seconds=sleep)
#         peers = core.find_job(self.qual_name(), 'running')
#         self.logger.info('found [%d] peer jobs', len(peers))
#         while datetime.datetime.now() < t1:
#             time.sleep(0.25)
#             tx = datetime.datetime.now() - t0
#             p = float(tx.total_seconds()) / float(sleep)
#             if p > 1.0:
#                 p = 1.0
#             self.progress(p, "[%1.0f%%] - slept [%d']", p * 100.0,
#                           tx.total_seconds())
#             if verbose:
#                 self.logger.info('be verbose at [%1.0f%%] - slept [%d]',
#                                  p * 100.0, tx.total_seconds())
#
# DEFER_FILE = '/tmp/_tester_defer_'
