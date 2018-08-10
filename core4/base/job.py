from core4.config.main import CoreConfig
from core4.base.main import CoreBase


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

    def __init__(self, **kwargs):

        self.author = "mkr"
        self.section = "job"

        # default_values
        self.defer_time = 600
        self.defer_max = 36000
        self.error_time = 3600
        self.adhoc = False
        # this syntax change in python3
        super().__init__()

        # defaults from the config take preceedence over class-defaults.
        self.load_config()

        # enqueueing arguments take preceedence over config-defaults.
        if kwargs:
            for key, value in kwargs.items():
                setattr(self, key, value)

    def load_config(self):
        for i in self.__dict__.keys():
            # needed as we do not want to overwrite our config
            if i != "config":
            # try:
                n = self.config.job.get(i)
                setattr(self, i, n)

    def serialize(self):
        tmp = self.__dict__
        tmp.pop('config')
        tmp['qual_name'] = self.qual_name()

        tmp['identifier'] = self.identifier
        return tmp
        #return tmp.pop('config')

    def deserialize(self, args={}):
        if args:
            for key, value in args.items():
                if key == '_id':
                    key = 'job_id'
                setattr(self, key, value)
        else:
            raise KeyError