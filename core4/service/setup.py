import os

from core4.base import CoreBase
import pymongo
from core4.util import Singleton

def once(f):
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return f(*args, **kwargs)
    wrapper.has_run = False
    return wrapper


class CoreSetup(CoreBase, metaclass=Singleton):

    @once
    def make_folder(self):
        """
        Creates the core4 folders defined with configuration key ``folder``.
        """
        root = self.config.folder.root

        def mkdir(folder):
            path = os.path.join(root, folder)
            if not os.path.exists(path):
                self.logger.warning("created folder [%s]", path)
                os.makedirs(path, exist_ok=True, mode=0o750)

        mkdir(self.config.folder.transfer)
        mkdir(self.config.folder.process)
        mkdir(self.config.folder.archive)
        mkdir(self.config.folder.temp)

    @once
    def make_role(self):
        # todo: requires implementation
        pass

    @once
    def make_queue(self):
        self.config.sys.queue.create_index(
            [
                ("name", pymongo.ASCENDING),
                ("_hash", pymongo.ASCENDING)
            ],
            unique=True,
            name="job_args"
        )
