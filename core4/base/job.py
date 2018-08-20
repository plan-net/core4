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


'''
This is the Job-Class of core4.
Every Job has to inherit from this.
It is only a container holding options.

delegation of options:
enqueue
|
environment-variables
|
config
|
Class-Defaults
'''


class CoreJob(CoreBase):





    def __init__(self, **kwargs):

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

    '''
    look and load config-values
    '''
    def load_config(self):
        for i in self.config.job:
            n = self.config.job.get(i)
            setattr(self, i, n)

    def serialize(self):
        """
        serialize a job for manifestating it within the mongo or any other document-store
        :returns json
        """
        serialize_args = ["job_args","nodes","priority","chain","tags","adhoc","defer_max",
                          "defer_time","error_time","dependency","max_parallel","wall_at","wall_time"]

        tmp = {}

        for i in serialize_args:
            tmp[i] = self.__getattribute__(i)


        return tmp
        # also do this explezitly

        #return tmp.pop('config')


    def deserialize(self, args={}):
        """
        Create a job out of a json document.
        """
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


    def progress(self):
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