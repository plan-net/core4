#
#Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
#This Source Code Form is subject to the terms of the Mozilla Public
#License, v. 2.0. If a copy of the MPL was not distributed with this
#file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import re
import tempfile

import shutil

import core4.util.data
from core4.queue.job import CoreJob


class CoreAbstractJobMixin:
    """
    Mix in this class to create an abstract job class. Abstract job classes
    are not listed in the job listing, e.g. extracted with ``coco --job``::

        class MyJobTemplate(CoreJob, CoreAbstractJobMixin):

            def method(self):
                # example method to be used by concrete classes inheriting
                # from MyJobTemplate
                pass
    """
    pass


class CoreLoadJob(CoreJob, CoreAbstractJobMixin):
    """
    This extended and abstracted :class:`.CoreJob` class provides additional
    methods for file management with folders ``transfer``, ``proc``, and
    ``archive``. It supports listing, filtering, moving and archiving helpers.
    """

    def _list_files(self, key, pattern=None, base=None):
        path = os.path.join(self.config.get_folder(key), base or self.project)
        if pattern is not None and isinstance(pattern, str):
            pattern = re.compile(pattern)
        if not os.path.exists(path):
            return []
        return sorted([os.path.join(path, f) for f in os.listdir(path) if
                       pattern is None or pattern.match(f) is not None])

    def _make_file(self, key, filename=None, base=None):
        if key == "temp":
            path = self.config.get_folder(key)
        else:
            path = os.path.join(self.config.get_folder(key),
                                base or self.project)
        if filename is None:
            filename = tempfile.mktemp(dir=path)
        (dirpart, filename) = os.path.split(filename)
        if dirpart:
            path = os.path.join(path, dirpart)
        fullname = os.path.join(path, filename)
        if not os.path.exists(path):
            self.logger.debug("make directory [%s]", path)
            os.makedirs(path)
        self.logger.debug("make file [%s]", fullname)
        return fullname

    def list_proc(self, pattern=None, base=None):
        """
        List all or matching files in the project's processing folder. If a
        regular expression pattern is passed, then it  applied as a filter. If
        ``base`` is set, then the project prefix is ignored the the passed base
        string is used as the prefix.

        :param pattern: str or regular expression to filter files
        :param base: path prefix to use instead of project name
        :return: list of matching file names
        """
        return self._list_files("process", pattern, base)

    def list_transfer(self, pattern=None, base=None):
        """
        List all or matching files in the project's transfer folder. If a
        regular expression pattern is passed, then it  applied as a filter. If
        ``base`` is set, then the project prefix is ignored the the passed base
        string is used as the prefix.

        :param pattern: str or regular expression to filter files
        :param base: path prefix to use instead of project name
        :return: list of matching file names
        """
        return self._list_files("transfer", pattern, base)

    def make_proc(self, filename, base=None):
        """
        Returns the full filename of a file in the project`s processing folder.
        If a ``base`` is passed, then the project name is ignored as the path  prefix
        and this ``base`` prefix is applied.

        :param filename: file to address
        :param base: path prefix to use instead of project name
        :return: full filename
        """
        return self._make_file("process", filename, base)

    def make_transfer(self, filename, base=None):
        """
        Returns the full filename of a file in the project`s transfer folder.
        If a ``base`` is passed, then the project name is ignored as the path
        prefix and this ``base`` prefix is applied.

        :param filename: file to address
        :param base: path prefix to use instead of project name
        :return: full filename
        """
        return self._make_file("transfer", filename, base)

    def make_temp(self, filename=None):
        """
        Returns the full filename of a file in the temp folder. If not
        ``filename`` is passed or is ``None``, then a temporary file is
        retrieved.

        :param filename: optional file to address, if ``None`` then a temporary
            file name is created and returned
        :return: full filename
        """
        return self._make_file("transfer", filename)

    def _move(self, source, key, base):
        filename = os.path.basename(source)
        temp_target = self._make_file(key, None, base)
        target = self._make_file(key, filename, base)
        shutil.move(source, temp_target)
        os.rename(temp_target, target)
        self.logger.debug("moved [%s] into [%s]: %s", filename, key, target)
        return target

    def move_transfer(self, source, base=None):
        """
        Move the source (full file name) into the ``transfer`` folder.  If a
        ``base`` is passed, then the project name is ignored as the path prefix
        and this ``base`` prefix is applied.

        :param source: full filename to move
        :param base: path prefix to use instead of project name
        :return: full target filename
        """
        return self._move(source, "transfer", base)

    def move_proc(self, source, base=None):
        """
        Move the source (full file name) into the ``processing`` folder.  If a
        ``base`` is passed, then the project name is ignored as the path prefix
        and this ``base`` prefix is applied.

        :param source: full filename to move
        :param base: path prefix to use instead of project name
        :return: full target filename
        """
        return self._move(source, "process", base)

    def move_archive(self, source, compress=True, base=None):
        """
        Move the source (full file name) into the ``archive`` folder.  If a
        ``base`` is passed, then the project name is ignored as the path prefix
        and this ``base`` prefix is applied.

        Additionally the prefix/base path name inside the ``archive`` folder
        is extended into a sub folder as specified by core4 configuration
        setting ``job.archive_stamp``. By default this additional prefix is
        ``{year:04d}/{month:02d}/{day:02d}/{_id:s}``.

        :param source: full filename to move
        :param compress: compress the file in the archive folder, defaults to
            ``True``
        :param base: path prefix to use instead of project name
        :return: full target filename
        """
        if self.started_at is None or self._id is None:
            raise RuntimeError("archiving requires .start_at and job ._id")
        filename = os.path.basename(source)
        path = os.path.join(self.config.get_folder("archive"),
                            base or self.project)
        kwargs = {
            "year": self.started_at.year,
            "month": self.started_at.month,
            "day": self.started_at.day,
            "hour": self.started_at.hour,
            "minute": self.started_at.minute,
            "_id": str(self._id),
        }
        path = path
        stamp = self.config.job.archive_stamp
        if stamp is not None:
            path = os.path.join(path, stamp.format(**kwargs))
        if not os.path.exists(path):
            os.makedirs(path)
        temp_filename = tempfile.mktemp(dir=path)
        temp_target = os.path.join(path, temp_filename)
        target = os.path.join(path, filename)
        shutil.move(source, temp_target)
        os.rename(temp_target, target)
        if compress:
            target = core4.util.data.compress(target)
        self.logger.info("archived [%s]: %s", filename, target)
        return target
