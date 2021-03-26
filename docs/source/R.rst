##############
CoreRJob
##############

Within core4, the most straightforward way to run R code is through the class :mod:`CoreRJob`.

As an example, let's say we want to...

* pass details about a database (here, a collection in MongoDB) from a core4 job to an R script,
* fetch the data and perform operations on it within the R script,
* and finally, return the results to the job

There are 2 ways in which this can be done:

**1. Having your entire logic in an R script**

pyscript.py:

.. code:: python

    from core4.queue.helper.job.r import CoreRJob

    class MyRJob(CoreRJob):
        author = "sjo"

        def execute(self):
            test_param = "random string"
            ret = self.r(source="rscript.R", # the source specifies the path of the R script to use
                         py_test_param=test_param) # we can also pass variables from python to R in the form of parameters

            # the control is now passed over to the R script

            self.logger.info("Result 1:\n", ret[0]) # result_df_1 from the R script
            self.logger.info("Result 2:\n", ret[1]) # result_df_2 from the R script


    if __name__ == '__main__':
        from core4.queue.helper.functool import execute
        execute(MyRJob)

rscript.R:

.. code:: r

    library(mongolite)

    r_test_param <- {{ py_test_param }} # variables passed from python are thus captured in R

    conn <- mongo(collection="{{ config.MyProject.MyCollection.name }}",
                  db="{{ config.MyProject.MyCollection.database }}",
                  url="{{ config.mongo_url }}")
                  # the R script can also directly access core4 configuration variables written in the form of jinja variables
    df <- conn$find()

    # core logic of the R script here
    # say we store the results of the operations into 2 dataframes, 'result_df_1' and 'result_df_2' respectively

    return(result_df_1)
    return(result_df_2) # we can thus return multiple dataframes / values to python


**2. Explicitly declaring an R session and calling specific functions within that session**

pyscript.py:

.. code:: python

    from core4.queue.helper.job.r import CoreRJob

    class MyRJob(CoreRJob):
        author = "sjo"

        def execute(self):
            rsession = self.get_rsession() # session with required libraries
            self.MyPythonFunction(rsession)

        def MyPythonFunction(self, rsession):
            collection_name = self.config.MyProject.MyCollection.name
            database_name = self.config.MyProject.MyCollection.database
            mongo_url = self.config.mongo_url

            rsession.source("rscript.R") # specify the path of the R script to use
            ret = rsession.MyRFunction(collection_name, database_name, mongo_url) # MyRFunction is in the R script
            # core4 configuration variables cannot directly be accessed by functions in an R session
            # therefore, they (as well as any other variables you want to pass to the R function) need to be passed as parameters

            # the control is now passed over to the R function

            self.logger.info("Result:\n", ret)


    if __name__ == '__main__':
        from core4.queue.helper.functool import execute
        execute(MyRJob)

rscript.R:

.. code:: r

    library(mongolite)

    MyRFunction <- function(collection, db, url){
        conn <- mongo(collection, db, url)
        df <- conn$find()

        # core logic of the R function here
        # say we store the results of the operations into the dataframe 'result_df'

        return(result_df) # the result is returned to the python program
    }

**Note:** In both approaches, the dataframe(s) we return to python cannot be nested. In case it is, a possible workaround is to "flatten" it by using a function such as :mod:`flatten()` from the :mod:`jsonlite` library in R before passing it to the python program.

Which of the two approaches to take can be decided based on the use case.

Approach 1 (entire logic in an R script) is useful if you want to...

* perform all your analyses in R and pass the end result to core4
* pass multiple results to core4
* have access to the core4 configuration in R

Approach 2 (running R functions run through a session) is useful if you want to to...

* implement the program's logic partly in python and partly in R, i.e. use selective functionality from R
* use functions from python and R in a non-serial order
