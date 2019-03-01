#############################################
frequently asked questions and best practices
#############################################

how to work with multiple core4 configuration
=============================================

The most simple approach to work with multiple core4 environments is to address
different core4 configuration YAML files with the environment variable
``CORE4_CONFIG``. If you have for example a configuration file
``~/,core4/local.yaml`` for development and another ``~/.core4/prod.yaml`` with
read-only connections to your production databases, then swith configuration
with::

    $ CORE4_CONFIG=~/.core4/local.yaml coco listing

or::

    $ export CORE4_CONFIG=~/.core4/local.yaml
    $ coco listing

and::

    $ CORE4_CONFIG=~/.core4/prod.yaml coco listing

or::

    $ export CORE4_CONFIG=~/.core4/prod.yaml
    $ coco listing


how to make a core4 job restartable
===================================

Restartability of a job is as simple as that:

#. assign a unique source using :meth:`.CoreLoadJob.set_source`.

   * If the source is a file and you do not have a unique filename, then make
     it unique while transfering the file from core4 ``transfer`` directory
     to core4 ``process`` directory (see :ref:`system_folder`).
   * If the source is not a file, then create a string representing the load.

#. if the job is restarted, ensure that all database collection records are
   removed before reloading the data. Use the records' ``_src`` attributes
   which represents the ``.set_source`` above.

If you job is not a load job, you can still apply the same mechanics. You just
have to think about the *scope* of your job. This could be the *daily* update
of a reporting collection, or a *weekly* update of or machine learning model.

Use this scope by setting the job source to this calender or month. If your
calculation or aggregation job needs to rerun or needs to be restarted, then
just purge all existing database records with the scope of this jobb. This is
then the *calender week and year* or the *month and the year* represented by
the job ``_src``.


how to parallelise a core4 job
==============================

See :doc:`parallel` and :doc:`example/prime` for a very concrete example
utilizing the *divide and conquer* design pattern.

