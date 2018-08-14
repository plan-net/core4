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

    def __init__(self, **kwargs):

        self._cookie = None

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

        do_not_modify = ["config", "plugin", "identifier", "_qual_name"]
        for i in self.__dict__.keys():
            if i not in do_not_modify:
            # we do have to make a distinction between explicit None in the config and None as no such key present.
            # try:
                n = self.config.job.get(i)
                setattr(self, i, n)

    def serialize(self):
        tmp = self.__dict__
        tmp.pop('config')
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


    # do we want this here or should this be done within the queue?
    def chain(self, job=[]):
        pass

    # will be set directly on __init__
    #def tag(self, tags=[]):


    nodes(Nodelist): set
    nodes
    to
    run
    on.
        setup_logger(Logger): specify



    # collection may not be needed as we would access it directly from within the config:
    # connect(mongodb://testcoll)

    # def collection(self, option=None, source=None, section=None, ro=False,
    #                setting=None, *args, **kwargs):
    #     """
    #     This method returns a mongo collection access object.
    #
    #     :param option: configuration option specifying the mongo collection uri
    #     :param source: source descriptor, mandatory for r/w access
    #     :param section: configuration section specifying the mongo collection uri
    #     :param ro: *True* for read-only access, *False* for read-/write access
    #     :return: :class:`.CoreJobCollection` object
    #     """
    #     if setting is None:
    #         if option is None:
    #             raise JobRuntimeError(
    #                 'job requires either config option or setting')
    #         setting = self.config.get_collection(option, section)
    #     coll = None
    #     if setting:
    #         # self.logger.debug('connecting to [mongodb://%s/%s/%s]',
    #         #                   ','.join(['%s:%d' % (k, v) for (k, v) in
    #         #                             setting['host']]),
    #         #                   setting['database'],
    #         #                   setting['collection'])
    #         if ro:
    #             coll = core.main.CoreCollection(setting, *args, **kwargs)
    #         else:
    #             if source is None or source.strip() == '':
    #                 raise JobRuntimeError, 'missing collection source'
    #             elif self.job_id is None:
    #                 raise JobStartupError, 'missing job id'
    #             ret = self.queue.add_source(self.job_id, source)
    #             coll = CoreJobCollection(setting, ret['source'], self.job_id,
    #                                      *args, **kwargs)
    #             if ret['modified']:
    #                 self.logger.debug('successfully assigned source [%s]',
    #                                   ret['source'])
    #             else:
    #                 self.logger.debug('source [%s] already assigned',
    #                                   ret['source'])
    #     return coll