###########################################################
calculation of prime numbers with Amazon Web Services (AWS)
###########################################################

The following job identifies prime numbers. Is is based on examples of Micha
Gorelick's and Ian Ozsvald's phantastic book *High Performance Python*.

The prime calculation is encapsulated in method ``check_prime`` which is used
by ``PrimeJob``.

Note that the job has two operating modes. If parameter ``size`` is
``not None``, then the range from ``start`` to ``end`` is split into equally
sized bins and a dedicated ``PrimeJob`` is enqueued for each bin.

If the job parameter ``size`` is ``None``, then the actual prime calculation
is executed::

    import math

    from core4.queue.helper.job.base import CoreLoadJob
    from core4.queue.helper.functool import enqueue

    def check_prime(n):
        if n % 2 == 0:
            return False
        from_i = 3
        to_i = math.sqrt(n) + 1
        for i in range(from_i, int(to_i), 2):
            if n % i == 0:
                return False
        return True


    class PrimeJob(CoreLoadJob):
        author = "mra"

        def execute(self, start, end, size=None, **kwargs):
            if size:
                for i in range(start, end, size):
                    e = i + size
                    if e > end:
                        e = end
                    enqueue(PrimeJob, start=i, end=e, **kwargs)
                return
            for i in range(start, end):
                self.progress(i/end)
                if check_prime(i):
                    print("found [%d]" %(i))
                    self.logger.info("found [%d]", i)


    if __name__ == '__main__':
        from core4.queue.helper.functool import execute
        execute(PrimeJob, start=1, end=1000000)


This job does not materialise any results. It has been used for the purpose of
performance studies with Amazon Web Services. The results of the study are
displayed below. As you can see, the performance scales almost linearly with
1, 2, 4 and 8 parallel worker nodes.

.. figure:: /_static/PrimeJob.png
   :scale: 100%
   :alt: PrimeJob Performance


The following Python code was used in an interactive IPython session to
generate the results::

    from core4.queue.helper.functool import enqueue
    from core4.base.main import CoreBase
    import datetime
    import time

    base = CoreBase()

    for s in range(0, 6):
        t0 = datetime.datetime.now()
        enqueue("mypro.job.PrimeJob", start=1, end=5000000, size=100000, run=s)
        while True:
            n = base.config.sys.queue.count_documents(
                    {"state": {"$in": ["running", "pending"]}})
            if n == 0:
                break
            time.sleep(1)
        t1 = datetime.datetime.now()
        print(s, (t1 - t0).total_seconds())


See also :doc:`aws/index` for a detailed walk-through on
*how to setup AWS with core4*.
