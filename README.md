core4
===== 

Project Installation inkl. core4

core4 nur Basis Installation
    sys.queue management muss in das Environment wechseln
    worker muss für .execute in das Environment wechseln
    process muss mehr machen als jetzt (ab job_factory)
    
    
der app server muss alle Projekte importen können damit er die Requests 
    einbinden kann

how to handle app servers' different dependencies
=> run one app serve_all for each project

how to handle enqueue and restart which are project dependent
=> wrap with a pickup script running in the project environment

how to know about installed projects
=> have a home directory to search from

how to setup project development
=> clone project
=> create python virtual environment
=> enter environment
=> install requirements
=> install core4 or set PYTHONPATH

    
prerequisites 
-------------

core4 requires on the following prerequisites.

* Python 3.5
* MongoDB database instance version 3.6.4 or higher up-and-running, 
  download from https://www.mongodb.com/download-center#community
* pip and git


installation scenarios
----------------------

The following step-by-step guide introduces three different scenarios to 
run/deploy core4:


1. DEVELOP AND MAINTAIN CORE4 PROJECTS. 
    
This scenario runs a core4 environment and works with a local or remote git 
project clone. In this scenario the core4 developer builds and distributes 
core4 project releases.


2. CORE4 PRODUCTION. 

In this scenario the core4 framework and one or more projects share one core4
scheduler, multiple core4 workers, one or more core4 app containers hosting
ReST APIs and core4 widgets based on the tornado web framework/asynchronous 
networking library.


3. CORE4 FURTHER DEVELOPMENT.

In this scenario you goal is to further develop core4. This is either
standalone core4 implementation work or in combination with a shared or private
project repository.

.. todo:: how to pull request


develop and maintain core4 projects
-----------------------------------

In this scenario we will install core4 in ~/core4.home, create, setup, build
and release a core4 project called "mypro".

Ensure all dependencies have been installed. This is Python 3.5, MongoDB, pip 
and git. Open up a shell and execute the following commands to install core4:

    # create core4 home                                                 #[1]# 
    mkdir ~/core4.home
    cd ~/core4.home
    
    # download setup script                                             #[2]#
    export CORE4_REMOTE=ssh://git.bi.plan-net.com/srv/git/core4.git
    export CORE4_BRANCH=mra.env
    git archive --remote $CORE4_REMOTE $CORE4_BRANCH croll.py | tar -xO > croll.py
    
    # create core4 environment                                          #[3]#
    python3 croll.py core4 $CORE4_REMOTE@$CORE4_BRANCH

    # enter core4 environment                                           #[4]#
    . core4/bin/activate


Within core4 environment you can create and develop your project. Chose project 
name "mypro" and create your test project with:

    # create new project
    coco --init mypro "My first core4 project"                          #[5]#


This has created the followinhg project structure:

    mypro/
    ├── README.md
    ├── enter_env
    ├── setup.py
    ├── install_requires.txt
    ├── requirements.txt
    ├── mypro
    │   ├── __init__.py
    │   └── mypro.yaml
    └── tests


This represents the bare project directory structure. Hidden directories
.git, .repos, and .venv are available, too.

At mypro/.repos resides the git repository. Directory mypro/.git contains your
git loacal worktree and the Python virtual environment is in mypro/.venv. 
    
These directories are only created if they do not exist and unless your 
worktree is connected to a remove git repository. In this case, .git carries
the connection to the remote repository and .repos does not exist.

Finally, `coco --init` has created an intial ~/.core4/local.yamlo configuration
file if it does not exist. The default values for your local MongoDB, logging
defaults and the location of folder.home are injected. The file is not 
modified if it already exists.

    DEFAULT:                                                            #[6]#
      mongo_url: mongodb://core:654321@localhost:27017
      mongo_database: core4dev
    
    logging:                                                            #[7]#
      mongodb: INFO
      stderr: DEBUG
      stdout: ~
    
    folder:                                                             #[8]#
      home: /home/mra/PycharmProjects
    

Enter the project's Python virtual environment

    # enter mypro environment                                           #[9]#
    source mypro/enter_env    


Start a worker in a shell:

    coco --worker                                                       #[10]#


Test to enqueue a simple default job

    # test enqueue                                                      #[11]#
    coco --enqueue core4.queue.helper.job.DummyJob


After successful execution show the job details from sys.queue and halt the
worker.
    
    # show details                                                      #[12]#
    coco --detail <job-id>

    # stop the worker                                                   #[13]#
    coco --halt


Now developement. Let's create our own test job. Switch to the git develop 
branch following the gitflow (see 
https://nvie.com/posts/a-successful-git-branching-model/:

    git checkout develop                                                #[14]#
    touch mypro/myjob.py


and paste the following snippet into the body of myjob.py:
    
    import core4.queue.job
    import time
    
    
    class MyJob(core4.queue.job.CoreJob):
        author = "mra"
    
        def execute(self, **kwargs):
            self.logger.info("hello world")
            for i in range(0, 10):
                time.sleep(1)
                self.progress(i / 10.)
                print("loop interval", i)
    
    
    if __name__ == '__main__':                                  
        from core4.queue.helper.functool import execute
        execute(MyJob)                                                  #[15]#


Save and close the file. Your development project should now look like this:

    mypro/
    ├── README.md
    ├── enter_env
    ├── setup.py
    ├── install_requires.txt
    ├── requirements.txt
    ├── mypro
    │   ├── __init__.py
    │   ├── mypro.py            # new file
    │   └── mypro.yaml
    └── tests


Directly execute the job with starting myjob.py directly as in:

    python mypro/myjob.py                                               #[16]#
    

Develop with your favorite IDE. Do not forget to address the correct Python
from .venv/bin/python and correct settings in local.yaml.

Running a background worker allows direct use of the execution framework 
addressing the job with its fully qualified name "mypro.myjob.MyJob".

    coco --enqueue mypro.myjob.MyJob                                    #[17]#


Now that we are happy with the job, let's build a release. We simulate the
typical deployment workflow for new features and bug fixing.
  
    # use develop branch for further development                        #[18]#
    git checkout develop                                        

    # add myjob.py                                                      #[19]#
    git add .

    # commit all changes                                                #[20]#
    git commit
    
    # build release 0.0.2                                               #[21]#
    coco --build


Finalize the release and merge branch release-0.0.2 into branches develop and
master:
    
    # merge release into develop                                        #[22]#
    git checkout develop
    git merge release-0.0.2

    # merge release into master                                         #[23]#
    git checkout master
    git merge release-0.0.2
    
    # publish the release                                               #[24]#
    coco --release


This rather long and at first sight complicated workflow is straight forward if
you follow the gitflow concept. As a recap this summary outlines the most 
relevant steps of this guideline so far.

    1. create home for core4 source and projects (lines #1 and #2).

    2. manage multiple dedicated Python virtual environments.
 
       * one for core4 (line #3)
       * one for each project (line #5)
       * use coco --init as the helper tool to initialise the environment (line
         #5)
       * enter and develop in project virtual environments (lines #4 and #9)

    3. manage your local.yaml for MongoDB connection (line #6), logging (line
       #7) and core4 project residence (line #8).

    4. develop with your favorite IDE, execute, and enqueue start jobs (lines 
       #10 through #13 and #15 through #16).
    
       * use git branching feature (lines #14 and #18)
       * push your changes into develop branch (lines #15, #19 and #20)
       
    5. Align and build new release with `coco --build` (line #21).
    
    6. After successful tests & QA merge your source changes from release-0.0.2
       to branches develop (line #22) and master (line #23) and finally rollout 
       the release with `coco --release` line  (line #24).


core4 production
----------------

This scenario is very similar to the previous scenario. The basic principles 
to run core4 and projects in production 

    # create core4 production home                                      #[1]# 
    mkdir ~/core4.prod
    cd ~/core4.prod
    
    # download setup script                                             #[2]#
    export CORE4_REMOTE=ssh://git.bi.plan-net.com/srv/git/core4.git
    export CORE4_BRANCH=mra.env
    git archive --remote $CORE4_REMOTE $CORE4_BRANCH croll.py | tar -xO > croll.py
    
    # install core4
    python3 croll.py core4 ssh://git.bi.plan-net.com/srv/git/core4.git@mra.env

    # install mypro
    python3 croll.py mypro file:///home/mra/core4.home/mypro/.repos

    # install another project
    python3 croll.py pro2 file:///home/mra/core4.home/pro2/.repos


Be sure to update your local.yaml core4 project home residence:

    folder:
      home: /home/mra/core4.prod


core4 further development
-------------------------

In this scenario we will develop core4 and project sources in ~/core4.dev, 
create, setup, make pull requests (TODO!), build and release core4 source code
and core4 projects.

Ensure all dependencies have been installed. This is Python 3.5, MongoDB, pip 
and git. Open up a shell and execute the following commands to develop core4:

    # create core4 IDE project                                          #[25]# 
    mkdir ~/PycharmProjects
    cd ~/PycharmProjects
    
    # clone core4                                                       #[26]#
    git clone ssh://git.bi.plan-net.com/srv/git/core4.git core4dev

    # checkout develop branch                                           #[27]#
    cd core4dev
    git checkout develop

    # enter core4 environment                                           #[4]#
    . core4/bin/activate


Within core4 environment you can create and develop your project. Chose project 
name "mypro" and create your test project with:

    # create new project
    coco --init mypro "My first core4 project"                          #[5]#


This has created the followinhg project structure:

    mypro/
    ├── README.md
    ├── enter_env
    ├── setup.py
    ├── install_requires.txt
    ├── requirements.txt
    ├── mypro
    │   ├── __init__.py
    │   └── mypro.yaml
    └── tests


This represents the bare project directory structure. Hidden directories
.git, .repos, and .venv are available, too.

At mypro/.repos resides the git repository. Directory mypro/.git contains your
git loacal worktree and the Python virtual environment is in mypro/.venv. 
    
These directories are only created if they do not exist and unless your 
worktree is connected to a remove git repository. In this case, .git carries
the connection to the remote repository and .repos does not exist.

Finally, `coco --init` has created an intial ~/.core4/local.yamlo configuration
file if it does not exist. The default values for your local MongoDB, logging
defaults and the location of folder.home are injected. The file is not 
modified if it already exists.

    DEFAULT:                                                            #[6]#
      mongo_url: mongodb://core:654321@localhost:27017
      mongo_database: core4dev
    
    logging:                                                            #[7]#
      mongodb: INFO
      stderr: DEBUG
      stdout: ~
    
    folder:                                                             #[8]#
      home: /home/mra/PycharmProjects
    

Enter the project's Python virtual environment

    # enter mypro environment                                           #[9]#
    source mypro/enter_env    


Start a worker in a shell:

    coco --worker                                                       #[10]#


Test to enqueue a simple default job

    # test enqueue                                                      #[11]#
    coco --enqueue core4.queue.helper.job.DummyJob


After successful execution show the job details from sys.queue and halt the
worker.
    
    # show details                                                      #[12]#
    coco --detail <job-id>

    # stop the worker                                                   #[13]#
    coco --halt


Now developement. Let's create our own test job. Switch to the git develop 
branch following the gitflow (see 
https://nvie.com/posts/a-successful-git-branching-model/:

    git checkout develop                                                #[14]#
    touch mypro/myjob.py


and paste the following snippet into the body of myjob.py:
    
    import core4.queue.job
    import time
    
    
    class MyJob(core4.queue.job.CoreJob):
        author = "mra"
    
        def execute(self, **kwargs):
            self.logger.info("hello world")
            for i in range(0, 10):
                time.sleep(1)
                self.progress(i / 10.)
                print("loop interval", i)
    
    
    if __name__ == '__main__':                                  
        from core4.queue.helper.functool import execute
        execute(MyJob)                                                  #[15]#


Save and close the file. Your development project should now look like this:

    mypro/
    ├── README.md
    ├── enter_env
    ├── setup.py
    ├── install_requires.txt
    ├── requirements.txt
    ├── mypro
    │   ├── __init__.py
    │   ├── mypro.py            # new file
    │   └── mypro.yaml
    └── tests


Directly execute the job with starting myjob.py directly as in:

    python mypro/myjob.py                                               #[16]#
    

Develop with your favorite IDE. Do not forget to address the correct Python
from .venv/bin/python and correct settings in local.yaml.

Running a background worker allows direct use of the execution framework 
addressing the job with its fully qualified name "mypro.myjob.MyJob".

    coco --enqueue mypro.myjob.MyJob                                    #[17]#


Now that we are happy with the job, let's build a release. We simulate the
typical deployment workflow for new features and bug fixing.
  
    # use develop branch for further development                        #[18]#
    git checkout develop                                        

    # add myjob.py                                                      #[19]#
    git add .

    # commit all changes                                                #[20]#
    git commit
    
    # build release 0.0.2                                               #[21]#
    coco --build


Finalize the release and merge branch release-0.0.2 into branches develop and
master:
    
    # merge release into develop                                        #[22]#
    git checkout develop
    git merge release-0.0.2

    # merge release into master                                         #[23]#
    git checkout master
    git merge release-0.0.2
    
    # publish the release                                               #[24]#
    coco --release


This rather long and at first sight complicated workflow is straight forward if
you follow the gitflow concept. As a recap this summary outlines the most 
relevant steps of this guideline so far.

    1. create home for core4 source and projects (lines #1 and #2).

    2. manage multiple dedicated Python virtual environments.
 
       * one for core4 (line #3)
       * one for each project (line #5)
       * use coco --init as the helper tool to initialise the environment (line
         #5)
       * enter and develop in project virtual environments (lines #4 and #9)

    3. manage your local.yaml for MongoDB connection (line #6), logging (line
       #7) and core4 project residence (line #8).

    4. develop with your favorite IDE, execute, and enqueue start jobs (lines 
       #10 through #13 and #15 through #16).
    
       * use git branching feature (lines #14 and #18)
       * push your changes into develop branch (lines #15, #19 and #20)
       
    5. Align and build new release with `coco --build` (line #21).
    
    6. After successful tests & QA merge your source changes from release-0.0.2
       to branches develop (line #22) and master (line #23) and finally rollout 
       the release with `coco --release` line  (line #24).




further reads
-------------

Find latest core4 documentation at http://bi.plan-net.com/core4 or build the
sphinx documentation with

    $ cd core4/docs
    $ make html


And Ensure you understand PROJECT ENVIRONMENTS and PROJECT STRUCTURE. There are 
sections dedicated to the main backend components of core4 running in 
environments and projects:

* PROJECT ENVIRONMENTS and PROJECT STRUCTURE
* JOBS, SCHEDULING and core4 WORKER
* the role of MONGODB IN SYSTEM CONTROL


On top of these backend components there are

* APP CONTAINERS
* the ReST API implementation guideline
* WIDGET organisation of endpoints


Irrespective of backend or frontend development, ensure you have a good 
understanding of core4 RELEASE MANAGEMENT to build and release core4 and 
project sources. As a developer as well as an operator you need to understand 
the core4 CONFIGURATION mechanics, LOGGING, AUTHORIZATION and ACCESS 
MANAGEMENT. 

* RELEASE MANAGEMENT
* CONFIGURATION MECHANICS
* LOGGING
* AUTHORIZATION AND ACCESS MANAGEMENT













    

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
