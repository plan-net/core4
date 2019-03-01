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
half. See :doc:`prime` which demonstrates this effect.

The collaboration between collection ``sys.queue``, the
:class:`worker <.CoreWorker>` and :class:`process <.CoreWorkerProcess>`
distributes multiple job execution requests between CPUs on the same compute
server and between compute servers in a core4 cluster.

The distributed and parallel job execution is applied to different job classes.
Special job properties like ``max_parallel`` and ``priority`` control
distrubted job execution inside and between nodes.

Parallel execution of the same task following the *divide and conquer* design
paradigm can be implemented with a simple design pattern. This design pattern
is demonstrated with :doc:`prime`. If inter-job communication is required, the
preferred transport layer is the MongoDB.


