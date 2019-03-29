############
Introduction
############

As of today, data scientists and modern data engineers use a variety of
`Python`_- and `R-Project`_-modules both open- and closed-source to create
relevant insights based on data from various sources. This ecosystem is
fueled by computational libraries like `Numpy`_, `Pandas`_, `Scikit-Learn`_ and
a wealth of libraries for visualization, and interactive notebooks like
`Bokeh`_ and `Jupyter`_.

However these packages do *not* support the data engineer or data scientist in
workflow automation, insight distribution, collaboration, and packaging.
Instead the Python data and analytics scene is more focused on the ad hoc
analysis aspect to answer single, specific business questions. If there is a
need for broader business applications, incorporating more than a single
business question, it is usually left to other teams like backend developers,
frontend developers and system administrators.

core4 fills this gap and enables the community to easily integrate their
processing chain of creating such insights into a fault-tolerant distributed
system and thereby automating the whole process without having to think about
underlying software or hardware.

The core4 framework takes care of everything that is essential to using and
operating such a distributed system, from central logging and configuration to
deployment, all this while scaling to the 100ths of servers.


Continue reading with

* a high-level :doc:`feature` of core4

* concrete :doc:`example/index` when and how to use core

* further details on :doc:`why` from

  #. data engieering perspective,

  #. data science perpective and

  #. business user and application perspective


Further information on python in data and analytics:
 * `The Incredible Growth of Python <https://stackoverflow.blog/2017/09/06/incredible-growth-python/>`_
 * `Why Python is Growing So Quickly <https://stackoverflow.blog/2017/09/14/python-growing-quickly/>`_

.. _Python: https://www.python.org/
.. _NumPy: http://www.numpy.org/
.. _Pandas: https://pandas.pydata.org/
.. _Scikit-Learn: http://scikit-learn.org/
.. _R-Project: https://www.r-project.org/
.. _Bokeh: https://bokeh.pydata.org/en/latest/
.. _Jupyter: https://jupyter.org/
