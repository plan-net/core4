.. _install:

############
installation
############

prerequisites
#############

core4 has on the following prerequisites.

* Linux flavour operating system
* Python 3.5
* MongoDB database instance version 3.6.4 or higher up-and-running,
  download from https://www.mongodb.com/download-center#community
* pip
* git

The following step-by-step guide describes the installation of these
requirements for operating systems Debian and Ubuntu.


Debian prerequisite installation guide
======================================

Debian 9 ships with Python 3. Check installation with::

    python3 --version


Install pip for Python 3, python-venv and git with::

    sudo apt-get install python3-pip python3-venv git


Install MongoDB and enable the service to start at boot time with::

    sudo apt-get install dirmngr
    sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 9DA31620334BD75D9DCB49F368818C72E52529D4
    echo "deb http://repo.mongodb.org/apt/debian stretch/mongodb-org/4.0 main" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.0.list
    sudo apt-get update
    sudo apt-get install -y mongodb-org
    sudo systemctl enable mongod


Protect MongoDB with a password of your choice.

.. note:: All core4 regression tests use username ``core`` with password
          ``654321`` on development desktops. Ensure your setup is reflected
          with your core4 ``local.yaml`` configuration file.


Pass the following javascript to the mongo shell. Ensure to update the username
and password if required::

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
lines::

    security:
      authorization: enabled


Finally restart mongod with::

    service mongod restart


Test settings and MongoDB connection now with::

    core --who
    mongo --username=core --password=654321 --authenticationDatabase admin
