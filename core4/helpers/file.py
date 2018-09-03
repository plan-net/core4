from core4.base.main import CoreBase
import core4.util
import os
import shutil
import zipfile
import gzip

class FileMixin(CoreBase):

    def get_file(self, dirname, filename=None, pattern=None):
        """
        Return a found directory or all files found within that directory.
        :returns directory or list of files.
        """
        # this is not used
        #if filename:
            #return os.path.join(dirname, filename)
        if pattern:
            return sorted([
                              os.path.join(dirname, f)
                              for f in os.listdir(dirname)
                              if pattern.match(f)])
        else:
            return dirname


    def move_arch(self, source, base=None, compress=True):
        """
        Moves the file to the account archive.

        With folder settings, the file ``/tmp/test.txt`` will be moved into
        ``/srv/core/arch/account/YYYY/MM/DD/HH.MM.SS/test.txt``.

        :param source: the full pathname of the source file
        :param base: an optional relative base directory to core's proc
                     directory, folders to the account name
        :param compress: compresses the source file, folder to True
        """
        if not os.path.exists(source):
            raise (RuntimeError('source [%s] not found' % (source)))
        basename = os.path.basename(source)
        # todo: this is currently not used
        # timestamp = None
        # if self.started is None:
        #     timestamp = core4.util.now()
        # else:
        #     timestamp = self.started
        # # archive root
        archive_dir = self.config.folder.root + "/" + self.config.folder.archive
        if not os.path.exists(archive_dir):
            raise (RuntimeError('archive root [%s] not found' % (archive_dir)))
        # archive directory
        target_dir = os.path.join(archive_dir,
                                  base or self.plugin,
                                  # todo: where is archive_timestamp configured ?
                                  # timestamp.strftime(
                                  #     self.config.get('archive_timestamp',
                                  #                     'folder')),
                                  str(self.job_id))
        if not os.path.exists(target_dir):
            self.logger.debug('creating [%s]', target_dir)
            os.makedirs(target_dir)
        # compression
        target = os.path.join(target_dir, basename)
        # todo: currently not possible due to
        # core4.error.Core4ConfigurationError: invalid type cast [archive_skip_compress] from [list] to [str]
#        for extension in self.config.folder.archive_skip_compress:
#            if target.lower().endswith(extension.lower()):
#                compress = False
#                self.logger.warning('skip compressing [%s]', source)
        if compress:
            target += '.gz'
        # target
        if os.path.exists(target):
            raise (RuntimeError('target [%s] exists' % (target)))
        # compression
        if compress:
            self.logger.debug('compressing [%s]', source)
            source = self.compress(source)
        # moving
        #
        # self.logger.debug('archiving [%s] to [%s]', source, target)
        shutil.move(source, target)
        self.logger.info('archived [%s]', target)
        return target

    def move_proc(self, source, base=None, overwrite=False):
        """
        Moves the file to the account processing folder.

        With folder settings, the file ``/tmp/test.txt`` will be moved into
        ``/srv/core/proc/account/test.txt``.

        :param source: the full pathname of the source file
        :param base: an optional relative base directory to core's proc
                     directory, folders to the account name
        :param compress: compresses the source file, folder to False
        """
        if not os.path.exists(source):
            raise (RuntimeError('source [%s] not found' % (source)))
        basename = os.path.basename(source)
        # root
        proc_dir = self.config.folder.root + "/" + self.config.folder.process
        if not os.path.exists(proc_dir):
            raise (RuntimeError('process root [%s] not found' % (proc_dir)))
        # process directory
        target_dir = os.path.join(proc_dir,
                                  base or self.plugin)
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
        proc_dir = self.config.folder.root + "/" + self.config.folder.process
        source_dir = os.path.join(proc_dir,
                                  base or self.plugin)
        if not os.path.exists(source_dir):
            raise (RuntimeError('process root [%s] not found' % (source_dir)))
        self.logger.debug('scanning [%s]', source_dir)
        return self.get_file(source_dir, pattern=pattern)

    def list_transfer(self, pattern=None, base=None):
        """
        Returns a filename in the account transfer directory. This method is
        useful if you just have the basename of a target file for the transfer
        directory.

        :param pattern: uses the regular expression to filter files in the
                        directory
        :param base: an optional relative base directory to core's transfer
                     directory, folders to the account name
        :return: the filename, directory name or list of full file names
        """
        transfer_dir = self.config.folder.root + "/" + self.config.folder.transfer
        source_dir = os.path.join(transfer_dir,
                                  base or self.plugin)
        if not os.path.exists(source_dir):
            raise (RuntimeError('process root [%s] not found' % (source_dir)))
        self.logger.debug('scanning [%s]', source_dir)
        return self.get_file(source_dir, pattern=pattern)

    def compress(self, filename):
        """
        Internal method to compress a file.

        :param filename: full filename
        """
        target = filename + '.gz'
        fin = open(filename, 'rb')
        fout = gzip.open(target, 'wb')
        fout.writelines(fin)
        fout.close()
        fin.close()
        os.remove(filename)
        return target

