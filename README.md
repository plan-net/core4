core4
===== 

download
--------

Download core4 by cloning the Git repository from its current location, i.e.::

    $ git clone ssh://git.bi.plan-net.com/srv/git/core4.git


prerequisites 
-------------
core4 depends on the following prerequisites.


* Python 3.5
* MongoDB database instance version 3.6.4 or higher up-and-running, 
  download from https://www.mongodb.com/download-center#community
* Python virtual environment. Install with ``pip install virtualenvwrapper``. 
  You need to update your shell environment, see for example
  http://virtualenvwrapper.readthedocs.io/en/latest/install.html on how to
  setup virtualenvwrapper.


create Python virtual environment
---------------------------------

Create a Python virtual environment with::

    $ mkvirtualenv core4 --python=python3.5
    

regression tests
----------------

The execution of regression tests require a MongoDB user ``core`` with password
``654321``.

    $ mongo admin --eval "db.createUser({'user': 'core', 'pwd': '654321', 'roles': [{'role': 'root', 'db': 'admin'}]})"

Change into core4 directory and execute regression tests with::

    $ cd core4
    $ python setup.py test

If all core4 Python dependencies are installed you can execute regression tests
also with::

    $ pytest
    

installation
------------

Install core4 and Python dependencies using pip::

    $ pip install .
    

or directly execute  ``setup.py`` with::

    $ python setup.py install


documentation
-------------

After successful installation of the core4 package you can build the
documentation (defaults to HTML format)::

    $ python setup.py sphinx
    
or directly execute the sphinx ``make`` command::

    $ cd ./docs
    $ make html
