core4
===== 


prerequisites 
-------------

core4 depends on the following prerequisites.

* Python 3.5
* MongoDB database instance version 3.6.4 or higher up-and-running, 
  download from https://www.mongodb.com/download-center#community
* pip
* git


installation
------------

Open up a shell and execute the following shell commands::

    # create core4 home directory 
    mkdir ~/core4
    cd ~/core4

    # install Python 3 virtual environment
    python3 -m venv core4

    # enter virtual environment
    source core4/bin/activate

    # install core4
    pip install git+ssh://git.bi.plan-net.com/srv/git/core4.git



.. todo:: document how to install and how to create core4 projects    


setup development environment on ubuntu
---------------------------------------

Install Pipenv following https://pipenv.readthedocs.io/en/latest/install/::

    $ pip install --user pipenv
    
Pipenv is still under heavy development. Upgrade the package often with::

    $ pip install --user --upgrade pipenv
    
Download core4 by cloning the Git repository from its current location, i.e.::

    $ git clone ssh://git.bi.plan-net.com/srv/git/core4.git

Setup your Python virtual environment with::

    $ cd core4
    $ pipenv install --python=3.5 -v -e .[tests]
    $ pipenv shell

Your're good to go now and extend core4 package.


setup development environment on debian
---------------------------------------


regression tests
----------------

The execution of regression tests require a MongoDB user ``core`` with password
``654321``.

    $ mongo admin --eval "db.createUser({'user': 'core', 'pwd': '654321', 'roles': [{'role': 'root', 'db': 'admin'}]})"

Change into core4 directory and execute regression tests with::

    $ cd core4
    $ pipenv shell


documentation
-------------

After successful installation of the core4 package you can build the
documentation (defaults to HTML format)::

    $ python setup.py sphinx
    
or directly execute the sphinx ``make`` command::

    $ cd ./docs
    $ make html
