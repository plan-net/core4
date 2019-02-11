######
R jobs
######

Today you have multiple options to integrate the power of R with the
flexibility of Python. core4 supports all alternatives.

The most straight forward option is to use a flat file as an air gap between
the two languages. This is described in detail at `integrating python and R`_.

More sophisticated options are described at `using Python and R together`_. For
core4 the package :mod:`rpy2` provides most flexibililty by using R within
core4 jobs.

The following example uses :mod:`pandas` to create a pandas dataframe,
activates the pandas/R integration module, and calculates a regression model
in R.

The example is based on the `minimal Python/R example`_. See also the
`Pandas/R interface`_.

.. _integrating Python and R: https://www.r-bloggers.com/integrating-python-and-r-into-a-data-analysis-pipeline-part-1/
.. _using Python and R together: https://www.kdnuggets.com/2015/12/using-python-r-together.html
.. _minimal Python/R example: https://stackoverflow.com/questions/30922213/minimal-example-of-rpy2-regression-using-pandas-data-frame
.. _Pandas/R interface: https://pandas.pydata.org/pandas-docs/version/0.22/r_interface.html

.. code-block:: python

    from core4.queue.job import CoreJob
    import pandas as pd
    from rpy2 import robjects as ro
    from rpy2.robjects import pandas2ri

    class RJob(CoreJob):

        author = "mra"

        def execute(self):
            pandas2ri.activate()
            R = ro.r
            df = pd.DataFrame({'x': [1,2,3,4,5],
                               'y': [2,1,3,5,4]})
            M = R.lm('y~x', data=df)
            self.logger.info(R.summary(M).rx2('coefficients'))
