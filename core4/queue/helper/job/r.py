import os
import shutil
import sys
from subprocess import Popen, PIPE

import feather
import numpy as np
import pandas as pd
from jinja2 import Environment, BaseLoader

import core4.error
import core4.error
from core4.queue.helper.job.base import CoreLoadJob
from core4.queue.helper.job.base import CoreAbstractMixin
# https://stackoverflow.com/questions/11716923/python-interface-for-r-programming-language
# https://www.kdnuggets.com/2015/10/integrating-python-r-data-analysis-part1.html

# install libraries

RSCRIPT = "/usr/bin/Rscript"
RLIB = "../lib/R"  # from Python executable
RLIBVAR = "R_LIBS_SITE"

SNIPPET = """

r = getOption("repos")
r["CRAN"] = "%s"
options(repos = r)
if(require('feather')==FALSE){
    install.packages('feather')
}
library(feather)

return <- function(v){
    write_feather(v, paste0("%s", "/out.", deparse(substitute(v))))
}
"""


class CoreRJob(CoreLoadJob, CoreAbstractMixin):

    def r(self, source=None, code=None, **kwargs):
        tempdir = self.make_temp_folder()
        script = os.path.join(tempdir, "script.r")
        exchange = {}
        for k, v in kwargs.items():
            if isinstance(v, pd.DataFrame):
                filename = os.path.join(tempdir, "in." + k)
                feather.write_dataframe(v, filename)
                value = 'read_feather("{}")'.format(filename)
            else:
                value = v
            exchange[k] = value
        snippet = SNIPPET % (self.config.rjob.cran_mirror, tempdir)
        if source is not None:
            if source.startswith("/"):
                source = os.path.join(self.project_path(), source[1:])
            else:
                source = os.path.join(os.path.dirname(self.module().__file__),
                                      source)
            code = open(source, "r").read()
        if code is not None:
            code = snippet + "\n\n" + code
            rtemplate = Environment(loader=BaseLoader).from_string(code)
            exchange["config"] = self.config
            exchange["tempdir"] = tempdir
            body = rtemplate.render(**exchange)
            self.logger.debug("execute R:\n%s", body)
            open(script, "w").write(body)
        else:
            raise core4.error.Core4UsageError(
                "either source or code parameter required")
        env = os.environ
        lib_path = os.path.join(os.path.dirname(sys.executable), RLIB)
        if os.path.exists(lib_path):
            if RLIBVAR in env:
                env[RLIBVAR] += ":" + lib_path
            else:
                env[RLIBVAR] = lib_path
        p = Popen([RSCRIPT, script], stdout=PIPE,
                  stderr=PIPE, env=env)
        (stdout, stderr) = p.communicate()
        self.logger.info("run in [%s]", tempdir)
        self.logger.info("stdout:\n%s\nstderr:\n%s",
                         stdout.decode("utf-8").strip(),
                         stderr.decode("utf-8").strip())
        result = []
        for outfile in os.listdir(tempdir):
            if outfile.startswith("out."):
                filename = os.path.join(tempdir, outfile)
                result.append(feather.read_dataframe(filename))
                self.logger.info("read outfile [%s]", filename)
        shutil.rmtree(tempdir)
        return tuple(result)

    def get_rsession(self):
        """
        This function initiates R session with all the required
        packages (in this example mongolite, openssl

        :return:
        """
        # activating this functio allows an automotized transfer
        # from R dataframes to pandas dataframe

        import rpy2.robjects.packages as rpackages
        from rpy2.robjects import pandas2ri
        from rpy2 import robjects as ro

        lib_path = os.path.join(os.path.dirname(sys.executable), RLIB)
        pandas2ri.activate()
        base = rpackages.importr('base')
        base._libPaths(np.append(base._libPaths(), lib_path))
        return ro.r

    def as_rdf(self, df):
        """
        transform pandas data frame to  R dataframe
        :param df: pandas dataframe
        :return:
        """
        from rpy2 import robjects as ro
        from rpy2.robjects import pandas2ri
        from rpy2.robjects.conversion import localconverter
        with localconverter(ro.default_converter + pandas2ri.converter):
            r_df = ro.conversion.py2rpy(df)
        return r_df
