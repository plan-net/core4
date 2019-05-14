core4os - THE PYTHON INSIGHT PLATFORM
=====================================

Develop, Operate and Collaborate on Data and Analytics

Automated - Flexible - Secure - Scalable


As of today, modern Data-Scientists use a variety of python- and R-modules both 
Open- and Closed-Source to create relevant insights based on multiple sets of 
data from many different sources.

core4os enables these Data-Scientists and other users to easily integrate their 
processing chain of creating such insights into a fault-tolerant distributed 
system and thereby automating the whole process without having to think about 
underlying software or hardware.

core4os takes care of everything that is essential to using and operating such a 
distributed system, from central logging and configuration to deployment, all 
this while scaling to the 100ths of servers. This allows for rapid progress 
from development to production deployment and even enables the developer to 
quickly deploy a REST API based on the output of his data-processing and 
therefore provides a shortcut for creating beautiful frontend applications.


prerequisite installation guide
-------------------------------

core4os has on the following prerequisites:

* Linux flavour operating system
* Python 3.5
* MongoDB database instance version 3.6.4 or higher up-and-running,
  download from https://www.mongodb.com/download-center#community
* pip
* git

This step-by-step guide shows how to install and setup all required systems.

Debian 9 ships with Python 3. Check installation with:

    python3 --version


Install pip for Python 3, python-venv and git with:

    sudo apt-get install python3-pip python3-venv git


Install MongoDB and enable the service to start at boot time with:

    sudo apt-get install dirmngr
    sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 9DA31620334BD75D9DCB49F368818C72E52529D4
    echo "deb http://repo.mongodb.org/apt/debian stretch/mongodb-org/4.0 main" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.0.list
    sudo apt-get update
    sudo apt-get install -y mongodb-org
    sudo systemctl enable mongod


Protect MongoDB with a password of your choice. Note that all core4 regression 
tests use username ``core`` with password ``654321`` on development desktops. 
Ensure your setup is reflected with your core4 ``local.yaml`` configuration 
file.

Pass the following javascript to the mongo shell. Ensure to update the username
and password if required:

    mongo <<- EOF
    use admin
    db.createUser(
      {
        user: "core",
        pwd: "654321",
        roles: [ { role: "root", db: "admin" } ]
      }
    );
    EOF


Edit MongoDB configuration file ``/etc/mongod.conf`` and add the following
lines:

    security:
      authorization: enabled


Finally restart mongod with:

    service mongod restart


Test settings and MongoDB connection now with:

    mongo --username=core --password=654321 --authenticationDatabase admin

    
core4os installation 
--------------------

Clone and install core4os framework in a Python virtual environment:

    # clone core4os
    git clone https://github.com/plan-net/core4.git 

    # enter clone
    cd core4

    # create Python virtual environment
    python3 -m venv .venv

    # enter Python virtual environment
    source enter_env

    # install core4 in development mode
    pip install -e ".[tests]"


further reads
-------------

Find latest core4 documentation at https://core4os.readthedocs.io/en/latest/ 
or build the sphinx documentation yourself with

    cd core4
    pip install -e ".[tests]" 
    cd core4/docs
    make html


3rd party systems and licenses
------------------------------

All external packages used within core4 have their license placed within the 
``LICENSES`` directory.

Those most notably contain:

* pymongo
* pandas
* tornado
* sphinx

