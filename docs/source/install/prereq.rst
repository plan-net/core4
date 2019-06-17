###############################
prerequisite installation guide
###############################

core4 has on the following prerequisites:

* Linux flavour operating system, preferred :doc:`Debian 9 <quick>` or
  :doc:`Ubuntu 18.04 <ubuntu>`
* Python 3.5 or higher
* MongoDB database instance version 3.6 or higher up-and-running,
  see https://www.mongodb.com/download-center#community
* pip 18.1 or higher
* git 2 or higher

This step-by-step guide shows how to install and setup all required systems.

Debian 9 ships with Python 3. Check installation with::

    python3 --version


Install pip for Python 3, python-venv and git with::

    sudo apt-get install python3-pip python3-venv git python3-dev


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


core4 uses special features of MongoDB which are only available with MongoDB
version 3.6 and above. Furthermore replication must be set up with your MongoDB
instance.

.. note:: If you work with core4 in your development environment with a local
          MongoDB installed you can still set up replication. See for example
          `Deploy a Replica Set for Testing and Development`_


To setup your MongoDB as a replica set you have to add the following additional
lines to your ``/etc/mongod.conf``::

    replication:
        oplogSizeMB: 1000
        replSetName: rs0


Furthermore you have to initialise the replica set, for example using MongoDB's
shell ``mongo``::

    use admin
    var js = {
        _id: "rs0",
        members: [
            {
                _id: 0,
                host: "localhost:27017"
            }
        ]
    }
    rs.initialize(js)


Finally restart mongod with::

    service mongod restart


Test settings and MongoDB connection now with::

    mongo --username=core --password=654321 --authenticationDatabase admin


.. _Deploy a Replica Set for Testing and Development: https://docs.mongodb.com/manual/tutorial/deploy-replica-set-for-testing/
