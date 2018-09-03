from core4.base.main import CoreBase
import core4.util
import os
import shutil
import zipfile

class FileMixin(CoreBase):


    def move_arch(self, source, base=None, compress=True):
        """
        Moves the file to the account archive.

        With default settings, the file ``/tmp/test.txt`` will be moved into
        ``/srv/core/arch/account/YYYY/MM/DD/HH.MM.SS/test.txt``.

        :param source: the full pathname of the source file
        :param base: an optional relative base directory to core's proc
                     directory, defaults to the account name
        :param compress: compresses the source file, default to True
        """
        if not os.path.exists(source):
            raise (RuntimeError('source [%s] not found' % (source)))
        basename = os.path.basename(source)
        # timestamp
        timestamp = None
        if self.started is None:
            timestamp = core4.util.now()
        else:
            timestamp = self.started
        # archive root
        archive_dir = self.config.get('archive_directory', 'DEFAULT')
        if not os.path.exists(archive_dir):
            raise (RuntimeError('archive root [%s] not found' % (archive_dir)))
        # archive directory
        target_dir = os.path.join(archive_dir,
                                  base or self.account,
                                  timestamp.strftime(
                                      self.config.get('archive_timestamp',
                                                      'DEFAULT')),
                                  str(self.job_id))
        if not os.path.exists(target_dir):
            self.logger.debug('creating [%s]', target_dir)
            os.makedirs(target_dir)
        # compression
        target = os.path.join(target_dir, basename)
        for extension in self.config.get_list('archive_skip_compress',
                                              'DEFAULT'):
            if target.lower().endswith(extension.lower()):
                compress = False
                self.logger.warning('skip compressing [%s]', source)
        if compress:
            target += '.gz'
        # target
        if os.path.exists(target):
            raise (RuntimeError('target [%s] exists' % (target)))
        # compression
        if compress:
            self.logger.debug('compressing [%s]', source)
            source = core4.util.compress(source)
        # moving
        #
        # self.logger.debug('archiving [%s] to [%s]', source, target)
        shutil.move(source, target)
        self.logger.info('archived [%s]', target)
        return target

    def move_proc(self, source, base=None, overwrite=False):
        """
        Moves the file to the account processing folder.

        With default settings, the file ``/tmp/test.txt`` will be moved into
        ``/srv/core/proc/account/test.txt``.

        :param source: the full pathname of the source file
        :param base: an optional relative base directory to core's proc
                     directory, defaults to the account name
        :param compress: compresses the source file, default to False
        """
        if not os.path.exists(source):
            raise (RuntimeError('source [%s] not found' % (source)))
        basename = os.path.basename(source)
        # root
        proc_dir = self.config.get('process_directory', 'DEFAULT')
        if not os.path.exists(proc_dir):
            raise (RuntimeError('process root [%s] not found' % (proc_dir)))
        # process directory
        target_dir = os.path.join(proc_dir,
                                  base or self.account)
        if not os.path.exists(target_dir):
            self.logger.debug('creating [%s]', target_dir)
            os.makedirs(target_dir)
        # target
        target = os.path.join(target_dir, basename)
        if os.path.exists(target):
            if not overwrite:
                raise (RuntimeError('target [%s] exists' % (target)))
            self.logger.warning('overwriting [%s]', target)
        # moving
        self.logger.debug('moving [%s] to [%s]', basename, target)
        shutil.move(source, target)
        return target

    def list_proc(self, pattern=None, base=None):
        """
        Retrieves files in core processing directory.

        :param filename: locates the filename in the processing directory, if
                         *None*, the directory itself is returned
        :param pattern: uses the regular expression to filter files in the
                        directory
        :return: the filename, directory name or list of full file names
        """
        # root
        proc_dir = self.config.get('process_directory', 'DEFAULT')
        source_dir = os.path.join(proc_dir,
                                  base or self.account)
        if not os.path.exists(source_dir):
            raise (RuntimeError('process root [%s] not found' % (source_dir)))
        self.logger.debug('scanning [%s]', source_dir)
        return self.config.get_file(source_dir, pattern=pattern)

    def transfer_file(self, filename=None, base=None):
        """
        Returns a filename in the account transfer directory. This method is
        useful if you just have the basename of a target file for the transfer
        directory.

        :param filename: locates the filename in the transfer directory, if
                         *None*, the directory itself is returned
        :param base: an optional relative base directory to core's transfer
                     directory, defaults to the account name
        :return: the filename, directory name or list of full file names
        """
        d = self.config.get('transfer_directory', 'DEFAULT')
        tdir = os.path.join(d, base or self.account)
        if not os.path.exists(tdir):
            self.logger.debug('creating [%s]', tdir)
            os.makedirs(tdir)
        return self.config.get_file(tdir, filename)

    def uncompress(self, filename, ignore_error=True, folder=None):
        """
        Uncompresses the passed file. Supports ZIP at the moment.

        :param filename: compressed file name
        :param ignore_error: fails if the temporary directory exists, already
        :param folder: subfolder name to use for extraction
        :return: tuple of directory and manifest of uncompressed files
        """
        if not os.path.exists(filename):
            raise (IOError, 'file [%s] not found' % (filename))
        if zipfile.is_zipfile(filename):
            z = zipfile.ZipFile(filename)
            basename = os.path.basename(filename)
            if folder:
                temp_dir = self.config.get_temp_file(folder)
            else:
                temp_dir = self.config.get_temp_file(basename)
            if os.path.exists(temp_dir):
                if not ignore_error:
                    raise(RuntimeError, 'temporary unzip directory ' \
                                        '[%s] exists' % (temp_dir))
            else:
                os.makedirs(temp_dir)
            z.extractall(path=temp_dir)
            content = [f.filename for f in z.infolist()]
            return (temp_dir, content)
        else:
            raise(RuntimeError, 'unknown compression type [%s]' % (filename))
