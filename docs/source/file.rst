#################
files and folders
#################


core4 package structure
=======================

The directory structure of core4 repository is::

    core4
    ├── core4                        .. core4 source root
    │   ├── api                      .. ReST API
    │   │   └── v1                   .. current version
    │   │       ├── request          .. request handlers
    │   │       │   ├── queue        .. sys.queue handlers
    │   │       │   ├── role         .. sys.role handlers
    │   │       │   ├── standard     .. standard handlers
    │   │       │   │   └── template .. e.g. error, card, help
    │   │       │   └── _static      .. default assets, e.g. CSS files
    │   │       └── tool             .. http server tools
    │   ├── base                     .. base class with database connectivity
    │   ├── config                   .. configuration management
    │   ├── logger                   .. logging
    │   ├── queue                    .. job framework
    │   ├── script                   .. command line tools
    │   ├── service                  .. system/service management
    │   │   ├── access               .. database access management
    │   │   ├── introspect           .. operating system introspection
    │   │   ├── operation            .. build/release management
    │   │   └── project              .. project management
    │   └── util                     .. general purpose utilities
    ├── demo                         .. demo project
    ├── docs                         .. sphinx documentation
    ├── other                        .. test project 1
    ├── project                      .. test project 2
    └── tests                        .. regression tests


core4 project structure
=======================

:ref:`coco --init <coco>` initialises a new core4 project repository. This
repository follows the Python best practice with the files ``README.md``,
``setup.py``, ``requirements.txt``, the source root and a ``tests`` directory.

Additionally a file ``enter_env`` is created to simplify entering the Python
virtual environment. Furthermore a special file ``install_requires.txt`` is
created. This file follows the same format as the known ``requirements.txt``
and is processed by ``setup.py``. For your convenience add all requirements
with optional version specs to this ``install_requires.txt``.

The directory structure of a core4 project repository is::

    mypro/
    ├── README.md                    ..
    ├── enter_env
    ├── setup.py
    ├── install_requires.txt
    ├── requirements.txt
    ├── mypro
    │   ├── __init__.py
    │   └── mypro.yaml
    └── tests


.. _system_folder:

core4 system folders
====================

core4 manages five working directories. These are defined with core4
configuration key ``folder``. The key ``folder.root`` defines the root folder
for these working directories. A relative path with ``folder.transfer``,
``folder.proc`` etc. is prefixed with the value of ``folder.root``.

The default ``folder.root`` is set to ``/tmp/core4`` and results in the
following folder locations:

* ``/tmp/core4/transfer`` - for files in transfer. Use this folder for all
  inbound and outbound file transfer.
* ``/tmp/core4/proc`` - for files to be processed. Use this folder for all
  files ready to process. See below on how to securely move files into this
  processing folder.
* ``/tmp/core4/archive`` - for processed files which have been archived. See
  below on how to securely archive processed files.
* ``/tmp/core4/temp`` - for temporary files. See below on how to simplify
  the creation of temporary files.

The abstract job :class:`.CoreLoadJob` facilitates the management of these
folders with the following methods:

* :meth:`list_transfer <core4.queue.helper.job.base.CoreLoadJob.list_transfer>`
  to enumerate files in the transfer folder
* :meth:`list_proc <core4.queue.helper.job.base.CoreLoadJob.list_proc>` to
  enumerate files in the processing folder
* :meth:`move_transfer <core4.queue.helper.job.base.CoreLoadJob.move_transfer>`
  to move a file into the processing folder. This method uses a temporary
  filename during file transfer and renames the file to the final target
  filename after the transfer has been completed. This mechanic _hides_ the
  files from all jobs scanning the processing folder while the file move is not
  finished.
* :meth:`move_proc <core4.queue.helper.job.base.CoreLoadJob.move_proc>` to move
  a file into the processing folder. The same move/rename mechanic of the
  previous method ``move_transfer`` apply here.
* :meth:`make_transfer <core4.queue.helper.job.base.CoreLoadJob.make_transfer>`
  to create a known or temporary filename in the transfer folder.
* :meth:`make_proc <core4.queue.helper.job.base.CoreLoadJob.make_proc>` to
  create a known or temporary filename in the processing folder
* :meth:`make_temp <core4.queue.helper.job.base.CoreLoadJob.make_temp>` to
  create temporary filename in the temp folder
* :meth:`move_archive <core4.queue.helper.job.base.CoreLoadJob.move_archive>`
  to archive and compress a processed file. Archiving applies an additional
  sub folders structure specified by core4 configuration key
  ``job.archive_stamp`` with the keys ``year``, ``month``, ``day``, ``hour``,
  ``minute``  and ``_id`` of the job's start time and job identifier archiving
  the file.

These helper methods enable the following workflow between a hypothetical
``DownloadJob`` and ``ImportJob``:

#. The ``DownloadJob`` accesses the source system (e.g. an sFTP site or web
   service) and creates the known file in the transfer folder
   ``/tmp/core4/transfer``.
#. After complete download, the ``DownloadJob`` calls method ``.move_proc``
   to securely move the downloaded file from the transfer into the processing
   folder ``/tmp/core4/proc``
#. The ``ImportJob`` independently scans the processing folder
   ``/tmp/core4/proc`` for new files matching a regular expression.
#. If a new file is found by the ``ImportJob`` the file is processed (e.g.
   imported into the database) and finally archived using method
   ``.move_archive``.

With this simple mechanic the ``ImportJob`` never starts processing of a file
which has not been completely transfered.


core4 home folder
=================

The special home folder specified by core4 configuration key ``folder.home``
locates all active projects. All valid core4 projects located in this folder
are in scope of the core4 runtime system with the core4 worker
(class:`.CoreWorker`), the scheduler (:class:`.CoreScheduler`) and the
web applications (functions :func:`serve` and :func:`serve_all`). You can
enumerate all projects and jobs with ``coco --project`` and ``coco --jobs``
(see :ref:`coco`) and manage jobs and API handlers which reside in this
core4 home directory.

.. note:: Please note that the home folder ``folder.home`` is not defined by
          default.
