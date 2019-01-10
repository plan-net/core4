core4
===== 

    
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

The scenario is further divided into two sub-scenarios: 1) the creation and
development of a new core4 project and 2) cloing and further developing an 
existing core4 project.


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


develop and maintain new core4 projects
---------------------------------------

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

Finally, `coco --init` has created an intial ~/.core4/local.yaml configuration
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


Directly execute the job with starting myjob.py as in:

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


develop and maintain existing core4 projects
--------------------------------------------

In this scenario we will clone, setup, build and release the existing core4 
project "mypro". This project has been created in the previous scenario under
~/core4.home/mypro.

Ensure all dependencies have been installed. This is Python 3.5, MongoDB, pip 
and git. Open up a shell and execute the following commands to clone the 
project:

    # create a development folder
    mkdir ~/core4.dev                                                   #[25]#                                           

    # clone core4 project
    cd ~/core4.dev
    git clone file:///home/mra/core4.home/mypro/.repos mypro            #[26]#

    # change to working tree                                            #[27]#
    cd ~/core4.dev/mypro


This has created the following file/folder structure:

    mypro/
    ├── .git                    # created by git clone
    ├── README.md
    ├── enter_env
    ├── setup.py
    ├── install_requires.txt
    ├── requirements.txt
    ├── mypro
    │   ├── __init__.py
    │   └── mypro.yaml
    └── tests


Finally you must create a Python virtual environment (line #28), enter it
(line #29) and install core4 (line #30) inside this environment. It is 
recommended to install the project itself in development mode (line #31):

    
    # create Python virtual environment                                 #[28]#
    python3 -m venv .venv
    
    # enter the environment                                             #[29]#
    source enter_env
    
    # install core4                                                     #[30]#
    pip install -U git+ssh://git.bi.plan-net.com/srv/git/core4.git@mra.env
    
    # install project mypro from current directory in development mode  #[31]#
    pip install -e .    


Do not forget to have a global core4 configuration file exists, for example at 
~/.core4/local.yaml.

    DEFAULT:                                                            
      mongo_url: mongodb://core:654321@localhost:27017
      mongo_database: core4dev
    
    logging:                                                            
      mongodb: INFO
      stderr: DEBUG
      stdout: ~
    
    folder:                                                             
      home: /home/mra/core4.dev
    

To test the job mypro.myjob.MyJob execute the following commands in two 
seperate shells:

    # Start worker in a shell
    coco --worker                                                       #[31]#

    # Directly execute the job 
    python mypro/myjob.py                                               #[32]#
    
    # enqueue job in another shell

    # enqueue job with coco
    coco --enqueue mypro.myjob.MyJob                                    #[33]#

    # stop the worker                                                   
    coco --halt                                                         #[34]#


core4 production
----------------

The basic principles to run core4 framework and projects in production is as
follows: 

    # create core4 production home                                      #[35]# 
    mkdir ~/core4.prod
    cd ~/core4.prod
    
    # download setup script                                             #[36]#
    export CORE4_REMOTE=ssh://git.bi.plan-net.com/srv/git/core4.git
    export CORE4_BRANCH=mra.env
    git archive --remote $CORE4_REMOTE $CORE4_BRANCH croll.py | tar -xO > croll.py
    
    # install core4                                                     #[37]#
    python3 croll.py core4 ssh://git.bi.plan-net.com/srv/git/core4.git@mra.env

    # install mypro                                                     #[38]#
    python3 croll.py mypro file:///home/mra/core4.home/mypro/.repos

    # install another project                                           #[39]#
    python3 croll.py pro2 file:///home/mra/core4.home/pro2/.repos


Be sure to update your local.yaml core4 project home residence:

    folder:
      home: /home/mra/core4.prod


core4 further development
-------------------------

To develop core4 further, you have to clone (line #40) the source code, create
a Python virtual environment (line #42), enter the environment (line #43) and
install core4 in development mode (line #44):

    # clone core4                                                       #[40]#
    git clone ssh://git.bi.plan-net.com/srv/git/core4.git
    
    # enter clone                                                       #[41]#
    cd core4
    
    # create Python virtual environment                                 #[42]#
    python3 -m venv .venv
    
    # enter Python virtual environment                                  #[43]#
    . enter_env 

    # install core4 in development mode                                 #[44]#
    pip install -e .


Be sure to have your ~/.core4/local.yaml.


build documentation
-------------------

Documentation requires the "tests" variant to setup:

    pip install -e .[tests]
    cd docs
    make html
    

regression tests
----------------

Regression tests require the "tests" variant to setup:

    pip install -e .[tests]
    pytest -x tests


further reads
-------------

Find latest core4 documentation at http://bi.plan-net.com/core4 or build the
sphinx documentation with

    $ cd core4/docs
    $ make html


Ensure you understand PROJECT ENVIRONMENTS and PROJECT STRUCTURE. There are 
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
