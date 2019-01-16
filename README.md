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
develop and rollout core4:


1. DEVELOP AND MAINTAIN CORE4 AND PROJECTS. 
    
This scenario runs a core4 environment and works with a local or remote git 
project clone. In this scenario the core4 developer builds and distributes 
core4 project releases.


2. DEPLOY PRODUCTION. 

In this scenario the core4 framework and one or more projects share one core4
scheduler, multiple core4 workers, one or more core4 app containers hosting
ReST APIs and core4 widgets based on the tornado web framework/asynchronous 
networking library.


3. FURTHER DEVELOPMENT OF CORE4 PROJECTS.

In this scenario you goal is to further develop existing core4 project. This is 
either standalone core4 implementation work or in combination with a shared or 
private project repository.

.. todo:: how to pull request


develop and maintain core4 projects and projects
------------------------------------------------

In this scenario we will install core4 in ~/core4.dev, create, setup, build
and release a core4 project called "mypro".

Ensure all dependencies have been installed. This is Python 3.5, MongoDB, pip 
and git. 

Open up a shell and execute the following commands to install core4:

    # create core4 home of your projects
    mkdir ~/core4.dev
    cd ~/core4.dev

    # clone core4                                                       
    git clone ssh://git.bi.plan-net.com/srv/git/core4.git
    
    # enter clone                                                       
    cd core4
    
    # create Python virtual environment                                 
    python3 -m venv .venv
    
    # enter Python virtual environment                                  
    . enter_env 

    # install core4 in development mode                                 
    pip install -e .[tests]


You can now create and develop your project. Chose project name "mypro" and 
create your test project with:

    # create new project
    cd ~/core4.dev
    coco --init mypro "My first core4 project"                          


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

In mypro/.repos resides the git repository. Directory mypro/.git contains your
git loacal working tree. The Python virtual environment is in mypro/.venv. 
    
These directories are only created if they do not exist and unless your 
worktree is connected to a remove git repository. In this case, .git carries
the connection to the remote repository and .repos does not exist.

Now is the time to create your local core4 configuration in 
~/.core4/local.yaml. Open your favorite editor or IDE and paste the following
content into this file. Ensure the configuration key "folder.home" addresses
the core4 home directory created above.

    DEFAULT:                                                            
      mongo_url: mongodb://core:654321@localhost:27017
      mongo_database: core4dev
    
    logging:                                                            
      mongodb: INFO
      stderr: DEBUG
      stdout: ~
    
    folder:                                                             
      home: /home/<username>/core4.dev
    
    worker:
      min_free_ram: 32


Enter the project's Python virtual environment:
    
    # exit core4 environment
    exit_env

    # enter mypro environment                                           
    . mypro/enter_env    


Start a worker in a shell:

    coco --worker                                                       


Test to enqueue a simple default job. Open up another shell, enter the 
environment for this shell, to and enqueue the DummyJob:

    # enter mypro environment (2nd shell)
    . core4.dev/mypro/enter_env
    
    # test enqueue                                                      
    coco --enqueue core4.queue.helper.job.DummyJob


After successful execution show the job details from sys.queue and halt the
worker.
    
    # show details                                                      
    coco --detail <job-id>

    # stop the worker                                                   
    coco --halt


Now developement. Let's create our own test job. Switch to the git develop 
branch following the gitflow (see 
https://nvie.com/posts/a-successful-git-branching-model/). 

    git checkout develop                                                
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
        execute(MyJob)                                                  


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

    python mypro/myjob.py                                               
    

Develop with your favorite IDE. Do not forget to address the correct Python
executable from .venv/bin/python and correct settings in local.yaml.

Running a background worker allows direct use of the execution framework 
addressing the job with its fully qualified name "mypro.myjob.MyJob".

    coco --enqueue mypro.myjob.MyJob                                    


Now that we are happy with the job, let's build a release. We simulate the
typical deployment workflow for new features and bug fixing.
  
    # use develop branch for further development                        
    git checkout develop                                        

    # add myjob.py                                                      
    git add .

    # commit all changes                                                
    git commit . -m "first job"
    
    # build release 0.0.2                                               
    coco --build


Finalize the release and merge branch release-0.0.2 into branches develop and
master:
    
    # merge release into develop                                        
    git checkout develop
    git merge release-0.0.2

    # merge release into master                                         
    git checkout master
    git merge release-0.0.2
    
    # publish the release                                               
    coco --release


This rather long and at first sight complicated workflow is straight forward if
you follow the gitflow concept. As a recap this summary outlines the most 
relevant steps of this guideline so far.

    1. create home for core4 source and projects.

    2. manage multiple dedicated Python virtual environments.
 
       * one for core4
       * one for each project
       * use coco --init as the helper tool to initialise the environment
       * enter and develop in project virtual environments

    3. manage your local.yaml for MongoDB connection, logging and core4 project 
       residence.

    4. develop with your favorite IDE, execute, and enqueue start jobs.
    
       * use git branching feature
       * push your changes into develop branch
       
    5. Align and build new release with `coco --build`.
    
    6. After successful tests & QA merge your source changes from release-0.0.2
       to branches develop and master and finally rollout the release with 
       `coco --release`.


core4 production
----------------

The basic principles to run core4 framework and projects in production is as
follows: 

    # create core4 production home                                       
    mkdir ~/core4.prod
    cd ~/core4.prod

    # create core4 project
    mkdir core4
    cd core4
    python3 -m venv .venv

    # activate environment
    . .venv/bin/activate    
    
    # install core4
    pip install git+ssh://git.bi.plan-net.com/srv/git/core4.git
    

Be sure to update your local.yaml core4 project home residence:

    folder:
      home: /home/mra/core4.prod


With a base installation of core4 you can now use core4's helper script
`cadmin` to deploy and upgrade core4 projects. The following example deploys
the "mypro" project we've developed (see above).

    cadmin --install -r file:///home/mra/core4.dev/mypro/.repos mypro


Check your setup with

    coco --who

    
Upgrade your setup with

    cadmin --upgrade 
   
   
Please note that for repositories which have not been created with `cadmin` you
have to manually upgrade. In our scenario this applies to the core4 project
itself which has been created in ~/core4.prod/core4. Use pip to upgrade your
installation:

    deactivate
    . ~/core4.prod/core4/.venv/bin/activate
    pip install --upgrade git+ssh://git.bi.plan-net.com/srv/git/core4.git   
        

develop and maintain existing core4 projects
--------------------------------------------

In this scenario we will clone, setup, build and release the existing core4 
project "mypro". This project has been created in the previous scenario under
~/core4.dev/mypro.

Open up a shell and execute the following commands to clone the project:

    # create a development folder
    mkdir ~/core4.dev2                                                                                              

    # clone core4 project
    cd ~/core4.dev2
    git clone file:///home/mra/core4.dev/mypro/.repos mypro             

    # change to working tree                                            
    cd mypro


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


Finally you must create a Python virtual environment, enter it and install 
core4 inside this environment. It is recommended to install the project itself 
in development mode:

    # create Python virtual environment                                 
    python3 -m venv .venv
    
    # enter the environment                                             
    source enter_env
    
    # install core4                                                     
    pip install -U git+ssh://git.bi.plan-net.com/srv/git/core4.git
    
    # install project mypro from current directory in development mode  
    pip install -e .    


Do not forget to have a global core4 configuration file at ~/.core4/local.yaml. 
See the example configuration yaml above.

To test the job mypro.myjob.MyJob execute the following commands in two 
seperate shells:

    # Start worker in a shell
    coco --worker                                                       

    # Directly execute the job 
    python mypro/myjob.py                                               
    
    # enqueue job in another shell
    coco --enqueue mypro.myjob.MyJob                                    

    # stop the worker                                                   
    coco --halt                                                         


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
