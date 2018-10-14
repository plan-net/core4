core4
===== 


prerequisites 
-------------
core4 depends on the following prerequisites.


* Python 3.5
* MongoDB database instance version 3.6.4 or higher up-and-running, 
  download from https://www.mongodb.com/download-center#community
* Pipenv - Python development workflows for humans. See 
  https://github.com/pypa/pipenv


Setup development environment
-----------------------------

Install Pipenv following https://pipenv.readthedocs.io/en/latest/install/::

    $ pip install --user pipenv
    
Pipenv is still under heavy development. Upgrade the package often with::

    $ pip install --user --upgrade pipenv
    
Download core4 by cloning the Git repository from its current location, i.e.::

    $ git clone ssh://git.bi.plan-net.com/srv/git/core4.git

Setup your Python virtual environment with::

    $ cd core4
    $ pipenv install --python=3.5 -v -e .[tests]

Your're good to go now and extned core4 apackage.


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
