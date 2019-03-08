##########################
data management and access
##########################

core4 uses Mongodb for system management and for project data management. To
support ad-hoc data engineering and analytics, core4 also provides custom
user databases.


core4 system collections
========================

core4 uses collections in MongoDB core4 database to manage the runtime
environment. The database name defaults to ``test`` and can be modified by
core4 configuration key ``DEFAULT.mongo_database``. The suggested name for the
production database is ``core4``.

The following collections enable system operations:

=========== ========================================
collection  purpose
=========== ========================================
sys.log     logging messages
sys.role    users and roles
sys.worker  registered workers
sys.job     registered jobs
sys.handler registered API request handlers
sys.cookie  cookies of jobs and API request handlers
sys.queue   job queue of active jobs
sys.lock    job processing lock
sys.journal job journal of processed jobs
sys.stdout  job stdout
sys.event   events
=========== ========================================

.. note:: Collection ``sys.stdout`` has a time-to-live (TTL) which can be
          defined by core4 configuration key ``worker.stdout_ttl``


project collections
===================

database name setting
---------------------

Best practice is to operate one MongoDB database for each project. The
suggested database name is the same as the project name.

The place to define this project database name is in the project YAML file,
e.g. ``demo.yaml``::

    DEFAULT:
      mongo_database: voting

    collection:
      client: !connect mongodb://client
      session: !connect mongodb://session
      event: !connect mongodb://event
      csv: !connect mongodb://csv


The above example defines the default database name ``voting``. This name
cascades into all ``!connect`` settings if no explicit database name is given.
See also :ref:`connect_tag`.


job load trace
--------------

A job extracts, downloads or retrieves data and feeds it into the job's project
MongoDB database. To trace data loads, each job must add source information
before inserting data into a MongoDB collection::

    for source in self.list_proc(".+\.csv$"):
        self.set_source(source)
        self.config.mypro.csv_collection.delete_many(
            {"_src": self.get_source()})
        df = pd.read_csv(source)
        self.config.mypro.csv_collection.insert_many(df.to_csv())


This snippet of a job queries all csv file in the processing folder, loads the
data using pandas, sets the source and finally inserts the data into the
MongoDB collection ``csv`` defined by core4 configuration setting
``mypro.csv_collection``::

    # content snippet of mypro.yaml
    DEFAULT:
      mongo_database: mypro
    csv_collection: !connect mongodb://csv


This mechanic of setting the source makes the data loaded from the csv file
traceable. Each csv line record carries an attribute ``_job_id`` and a source
identifier ``_src``. This approach also enables restartability of a job which
can be achieved by resetting all records in collection ``csv`` before
reoloading the data::

    self.config.mypro.csv_collection.delete_many(
        {"_src": self.get_source()})


.. note:: The ``_src`` attributes only stores the basename of the source
          filename.


user databases
==============

core4 authorization manages read-only access to MongoDB databases. See
:doc:`access`. Additionally each user has read/write access to his or her
user database. These databases adhere to the naming convention
``user![username]`` which can be modified with core4 configuration setting
``sys.userdb``.

To access the database an access token has to be created.
See :ref:`access_manager`. Use this token similar to a password to connect to
your personal user databbase::

    mongo \
        --host [hostname] \
        --port [port] \
        --username [username] \
        --password [token] \
        --authenticationDatabase admin
