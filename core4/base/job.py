from core4.config.main import CoreConfig
from core4.base.main import CoreBase
import core4.base.cookie


STATE_PENDING = 'pending'
STATE_RUNNING = 'running'
STATE_FAILED = 'failed'
STATE_DEFERRED = 'deferred'
STATE_ERROR = 'error'
STATE_COMPLETE = 'complete'
STATE_INACTIVE = 'inactive'
STATE_KILLED = 'killed'


'''
This is the Job-Class of core4.
Every Job has to inherit from this.
It is only a container holding options.

delegation of options:
enqueue
|
config
|
Class-Defaults
'''


class CoreJob(CoreBase):


    job_args = {}
    nodes = None
    priority = None
    chain = None
    tags = []
    adhoc = False
    defer_max = 36000
    defer_time = 600
    error_time = 3600
    dependency = None
    max_parallel = None
    wall_at = 0
    wall_time = 0



    def __init__(self, **kwargs):

        self._cookie = None
        self.author = "mkr"
        self.section = "job"


        super().__init__()


        # defaults from the config take preceedence over class-defaults.
        self.load_config()

        # enqueueing arguments take preceedence over config-defaults.
        if kwargs:
            for key, value in kwargs.items():
                setattr(self, key, value)

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

    '''
    look for config-values
    '''
    def load_config(self):
        for i in self.__dict__.keys():
            try:
                n = self.config.job.get(i)
                setattr(self, i, n)
            except:
                pass


    def serialize(self):
        serialize_args = ["job_args","nodes","priority","chain","tags","adhoc","defer_max",
                          "defer_time","error_time","dependency","max_parallel","wall_at","wall_time"]

        tmp = {}

        for i in serialize_args:
            tmp[i] = self.__getattribute__(i)


        return tmp
        # also do this explezitly

        #return tmp.pop('config')

    def deserialize(self, args={}):
        if args:
            for key, value in args.items():
                if key == '_id':
                    key = 'job_id'
                setattr(self, key, value)
        else:
            raise KeyError

    def __eq__(self, obj):
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
        Is the access layer to the job's cookie. See also :class:`.Cookie`.
        """
        if not self._cookie:
            self._cookie = core4.base.cookie.Cookie(self.qual_name())
        return self._cookie
