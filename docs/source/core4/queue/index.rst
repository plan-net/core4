#####
queue
#####

Package :mod:`core4.queue` with class :class:`core4.queue.job.CoreJob`
and :class:`core4.queue.worker.CoreWorker`` represent the basis to all core4
jobs. All classes derived from :class:`.CoreJob` ship with access to
configuration, data (see also :mod:`data access protocols <.connector>`), and
logging (see also :doc:`logging mechanics<../logger/index>`).


.. toctree::
   :caption: Table of Contents

   job
   worker
   process
   main
   query
