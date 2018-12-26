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

The following setup installs the core4 framework. This setup typically applies
to a development computer. See below how to setup core4 if you want to further 
develop the core4 source code. 

To install the framework open up a shell and execute the following shell 
commands:

    # create core4 home directory 
    mkdir ~/core4
    cd ~/core4

    # install Python 3 virtual environment
    python3 -m venv core4

    # enter virtual environment
    source core4/bin/activate

    # install core4
    pip install git+ssh://git.bi.plan-net.com/srv/git/core4.git@mra.ops


After successful installation you can create and develop core projects.

    
create core4 project
--------------------

Open up a shell and execute the following shell commands to create a new core4
project on your development computer. Please note that we first enter the core4 
Python virtual environment which we have created in the previous step. core4 
command utilities like ``coco`` are available then::

    # enter core4 Python virtual environment
    mkdir ~/core4
    cd ~/core4
    source core4/bin/activate
    
    # create new project
    coco --init project1 "test project 1" --yes
    

build project releases
----------------------

core4 build and release helpers support the gitflow best practice on your
development computer (see https://nvie.com/posts/a-successful-git-branching-model/): 
develop your project in branch "develop", build a release, merge the release in 
branches "develop" and "master" and finalise the release with a release tag:

    # enter project Python virtual environment
    cd ~/core4/project1
    . enter_env

    # checkout branch develop following the gitflow best practice
    git checkout develop
    
    # *** implement changes in project1 ***
    
    # build new release 0.0.2 
    coco --build
    
    # merge release-0.0.2 into branch develop
    git checkout develop
    git merge release-0.0.2
    
    # merge release-0.0.2 into branch master
    git checkout master
    git merge release-0.0.2
    
    # finalize the release
    coco --release
    
    # exit project environment
    exit_env
    
    
deploy core4 and projects
-------------------------

Follow these steps to setup core4 and any number of core4 projects. This setup
typically applies to your production servers:

    # create core4 production home 
    mkdir ~/core4.prod
    cd ~/core4.prod
    
    # download deployment script    
    export CORE4_REMOTE=ssh://git.bi.plan-net.com/srv/git/core4.git
    export CORE4_BRANCH=mra.ops
    git archive --remote $CORE4_REMOTE $CORE4_BRANCH croll.py | tar -xO > croll.py
    
    # deploy core4 framework
    python3 croll.py core4 $CORE4_REMOTE@$CORE4_BRANCH

    # local repository home
    export CORE4_HOME=~/core4

    # deploy project1
    python3 croll.py project1 file://$CORE4_HOME/project1/.repos

    # deploy project2
    python3 croll.py project2 file://$CORE4_HOME/project2/.repos

    source core4/bin/activate
    

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
