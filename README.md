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


install prerequisites
---------------------
core4os has on the following prerequisites:

* 64-bit Linux operating system, preferably Debian 9 or Ubuntu 18.04
* Python 3.5 or higher
* MongoDB database instance version 3.6 or higher up-and-running,
  see https://www.mongodb.com/download-center#community
* pip 18.1 or higher
* git 2 or higher
* Node.js 12 or higher
* yarn


Install pip for Python 3, python-venv and git with:

    # install prerequisites
    sudo -s
    apt-get update
    apt-get install python3-pip python3-venv python3-dev gcc make git dirmngr libffi-dev --yes


Install MongoDB and enable the service to start at boot time with:

    # install MongoDB
    sudo -s
    wget -qO - https://www.mongodb.org/static/pgp/server-4.4.asc | sudo apt-key add -
    echo "deb http://repo.mongodb.org/apt/debian "$(lsb_release -sc)"/mongodb-org/4.4 main" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.4.list
    apt-get update
    apt-get install -y mongodb-org
    systemctl start mongod # start MongoDB service
    systemctl status mongod # ensure that it has started succesfully
    systemctl enable mongod # ensure that it will start every time the system is booted

    # set a replica set configuration for MongoDB
    mongo # enter the MongoDB shell
    rs.initiate() # set the MongoDB server as the first member of a new replica set
    exit # exit the MongoDB shell

More details on installing MongoDB can be found on https://docs.mongodb.com/manual/tutorial/install-mongodb-on-debian/.   
Please note that MongoDB requires further configuration later. See below.

Install nodejs, yarn and npm to build and setup web tools:

    # install nodejs and npm
    sudo -s
    wget -qO- https://deb.nodesource.com/setup_12.x | bash -
    apt-get install -y nodejs


Install nodejs, yarn and npm to build and setup web tools:

    # install nodejs and npm
    sudo -s
    wget -qO- https://deb.nodesource.com/setup_11.x | bash -
    apt-get install -y nodejs
    
    # install yarn
    sudo -s
    wget -qO- https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
    echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list
    apt-get update
    apt-get install yarn --yes
    npm -g install vue-cli


install core4os
---------------
After you have installed the prerequisites continue to clone and install core4os
framework in a Python virtual environment:

    # clone core4
    git clone https://github.com/plan-net/core4.git

    # setup and enter Python virtual environment
    cd core4
    python3 -m venv .venv
    source enter_env

    # install core4
    python setup.py --fe

    # configure MongoDB for it to fit core4os' requirements
    python local_setup.py


test the core4os backend
-------------------------
Once core4os and all its dependencies are installed and configured, it's time to make sure that everything works as expected. This can be done as follows.

Run the core4 worker:

    coco --worker

Open a new terminal instance (do not close the previous one) and enter the previously created python virtual environment, list the available jobs, and run the test job `DummyJob`:

    source enter_env
    coco --job
    coco --enqueue core4.queue.helper.job.example.DummyJob

Once the job is enqueued, a job ID will be assigned to it and displayed in the terminal. You can check the details of any job by runnning the following command:

    coco --detail <job ID>


test the core4os frontend
-------------------------
In a new terminal instance, enter the python virtual environment and launch the core4 API container:

    source enter_env
    coco --app --filter core4.api.v1

The core4 widget manager will now be accessible at http://0.0.0.0:5001 with username and password **admin** (for both). Once logged in, there are several widgets available with which core4os can be used used graphically.


further reads
-------------
Find the latest core4os documentation at https://core4os.readthedocs.io/en/latest/
or build the sphinx documentation with

    cd core4
    pip install -e ".[tests]"
    cd core4/docs
    make html

Both methods of accessing the documentation provide further instructions on using core4os as well as a core4 installation guide for Ubuntu 18.04.


3rd party systems and licenses
------------------------------
All external packages used within core4os have the associated license placed
within the ``LICENSES`` directory.
