.. _parallel:

######################################
distributed and parallel job execution
######################################

With Python, the best and simplest way for true parallel job execution is to
run and manage multiple child processes in parallel using the :mod:`subprocess`
or the :mod:`multiprocessing` modules. The mechanics of these builtin modules
still limit parallel execution to the same computer.

core4 implements a simple queuing system to enable true parallel execution of
python code withing *and* across multiple computers.

This core4 feature implements linear scalability: doubling the number of
computers participating in a core4 cluster cuts the total execution time into
half. See :doc:`/example/prime` which demonstrates this effect.

The collaboration between collection ``sys.queue``, the
:class:`worker <.CoreWorker>` and :class:`process <.CoreWorkerProcess>`
distributes multiple job execution requests between CPUs on the same compute
server and between compute servers in a core4 cluster.

The distributed and parallel job execution is applied to different job classes.
Special job properties like ``max_parallel`` and ``priority`` control
distributed job execution inside and between nodes.

Parallel execution of the same task following the *divide and conquer* design
paradigm can be implemented with a simple design pattern. This design pattern
is demonstrated with :doc:`the PrimeJob example </example/prime>`. If inter-job
communication is required, the preferred transport layer is the MongoDB.

The following code snippet demonstrates the divide/conquer design patter with
core4. A job launched with ``chunksize not None`` will launch child jobs at
the first run (line 8 and line 9). It will then defer (line 10). Job execution
stops at this position. When the job is relaunched after its ``defer_time``
(line 3), it will monitor job execution of the children (line 11). The job
method ``.monitor`` is simple counting the number of running child jobs and
defer again, if any children are still up and running or pending (line 18-20).
This ``.monitor`` method should be extended in real-life applications to report
progress of the whole job chain using :meth:`.progress <.CoreJob.progress>`.

If no chunk size has been passed as a job parameter, this job is supposed
to do the actual work (line 12).

Plese note, that the actual implementation of ``.divide`` and ``.work`` have
been passed for brevitiy. Both methods of cause depend on the type and purpose
of the job. In the :doc:`PrimeJob example </example/prime>` for example the
``chunksize`` represents the lower and upper bound of prime number to test.

.. code-block:: python
   :linenos:

    class DivideAndConquer(CoreLoadJob):
        author = "mra"
        defer_time = 5
        max_parallel = 5

        def execute(self, chunksize=None, **kwargs):
            if chunksize:
                if self.trial == 1:
                    self.launch(chunksize)
                    self.defer("waiting")
                return self.monitor()
            self.work(**kwargs)

        def launch(self, chunksize):
            pass

        def work(**kwargs):
            pass

        def monitor(self):
            n = self.config.sys.queue.count_documents({"args.mid": str(self._id)})
            if n > 0:
                self.defer("[%d] job still running", n)
