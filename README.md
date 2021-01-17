core4os - THE PYTHON INSIGHT PLATFORM
=====================================

Develop, Operate and Collaborate on Data and Analytics

Automated - Flexible - Secure - Scalable


Data scientists use a variety of Python and R modules to create relevant 
insights based on multiple sets of data from many different sources. core4os 
enables data scientists and other users to integrate an existing 
insight-generation processing chain into a fault-tolerant, distributed system, 
thereby automating the whole data analytics process from data transformation to 
insight generation without the usual need to worry about the underlying software 
or hardware. 

core4os takes care of everything that is essential to using and operating such a 
distributed system, from central logging and configuration to deployment, all 
while scaling to hundreds of servers, allowing for rapid progress from 
development to production deployment and even enabling the developer to deploy a 
HTTP API quickly based on the output of the data-processing, which provides a 
shortcut for creating beautiful, frontend applications.


prerequisite installation guide
-------------------------------

core4os has on the following prerequisites:

* Linux flavor operating system, preferably Debian 9 or Ubuntu 18.04
* Python 3.5 or higher
* MongoDB database instance version 3.6 or higher up-and-running,
  see https://www.mongodb.com/download-center#community
* pip 18.1 or higher
* git 2 or higher


Install pip for Python 3, python-venv and git with:

    # install prerequisites
    su -
    apt-get update
    apt-get install python3-pip python3-venv python3-dev gcc make git dirmngr libffi-dev --yes


Install MongoDB and enable the service to start at boot time with:

    # install MongoDB (requires root privileges)
    apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 9DA31620334BD75D9DCB49F368818C72E52529D4
    echo "deb http://repo.mongodb.org/apt/debian "$(lsb_release -sc)"/mongodb-org/4.0 main" | tee /etc/apt/sources.list.d/mongodb.list
    apt-get update
    apt-get install mongodb-org --yes
    systemctl start mongod.service
    systemctl enable mongod.service

Please note that MongoDB requires further configuration. See below.


Install R to build and run R scripts:

    # install R (requires root privileges)
    apt install apt-transport-https gnupg2 --yes
    apt-key adv --keyserver keys.gnupg.net --recv-key 'E19F5F87128899B192B1A2C2AD5F960A256A04AF'
    add-apt-repository 'deb https://cloud.r-project.org/bin/linux/debian stretch-cran35/'
    apt update
    apt install r-base --yes


Install nodejs, yarn and npm to build and setup web tools:

    # install nodejs and npm (requires root privileges)
    wget -qO- https://deb.nodesource.com/setup_15.x | bash -
    apt-get install -y nodejs
    
    # install yarn (requires root privileges)
    wget -qO- https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
    echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list
    apt-get update
    apt-get install yarn --yes
    npm -g install vue-cli

    
core4os installation (backend only) 
-----------------------------------

After you have installed the prerequisites continue to clone and install core4os 
framework in a Python virtual environment. 

You should drop root privileges.

    exit  # exit root

    cd
    mkdir dev
    
    # clone core4
    git clone https://github.com/plan-net/core4.git
    
    # setup and enter Python virtual environment
    cd core4
    python3 -m venv .venv
    source enter_env

    # install wheel
    pip install wheel
    
    # install core4
    pip install --edit .
    

MongoDB setup
-------------

MongoDB requires further configuration to setup a replica set. core4os uses some 
special features of MongoDB which are only available with replica set.

The interactive script ``local_setup.py`` simplifies this configuration. Start 
the script with ``python local_setup.py`` in the Python virtual environment 
created above. 


further reads
-------------

Find the latest core4os documentation at https://core4os.readthedocs.io/en/latest/ 
or build the sphinx documentation with

    cd core4
    pip install -e ".[tests]" 
    cd docs
    make html
    
    
test your installation
----------------------

Launch a core4os worker and in a second terminal enqueue a DummyJob. This 
DummyJob just waits for let's say 30 seconds.

    # first shell in Python virtual environment
    coco --worker
    
    # second shell
    source enter_env
    coco --enqueue core4.queue.helper.job.example.DummyJob '{"sleep": 30}'
    
    # watch the job finishing
    watch -n 1 coco --list
    
    # stop the worker
    coco -x
    

View the documentation

    firefox docs/build/html/index.html

    
Launch the core4os HTTP server and in a second terminal 
login and call the API handler info resource.

    # first shell in Python virtual environment
    coco --app --filter core4.api.v1    
    
    # second shell to visit the API info endpoint 
    # with default username/password
    firefox "http://localhost:5001/core4/api/v1/_info?username=admin&password=admin"


web app installation
--------------------

tbd.


3rd party systems and licenses
------------------------------

All external packages used within core4os have the associated license placed 
within the ``LICENSES`` directory.
