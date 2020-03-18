################
regression tests
################

MongoDB protection
------------------

Please note that running the core4os regression tests requires two additional
steps. First, the user ``core`` must exists as a MongoDB user with password
``654321``. Second, the MongoDB hostname must have an additional domain name
``testmongo``. **For production the password and hostname must be changed.**


Ensure the setup is reflected with your core4os ``local.yaml`` configuration
file.

Pass the following JavaScript to the mongo shell to create user ``core`` with p
assword ``654321``:

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


Edit the MongoDB configuration file ``/etc/mongod.conf`` and add the following
lines:

    security:
      authorization: enabled



Add hostname ``testmongo`` to the ``/etc/hosts`` file:

    127.0.0.1   localhost
    127.0.0.1   testmongo


Finally, restart mongod with:

    service mongod restart


Test the settings and MongoDB connection with:

    mongo --username=core --password=654321 --authenticationDatabase admin


test package installation
-------------------------

Regression tests require the "tests" variant to setup::

    # clone core4
    git clone https://github.com/plan-net/core4.git

    # enter clone
    cd core4

    # create Python virtual environment
    python3 -m venv .venv

    # enter environment
    source enter_env

    # install test prerequisites
    pip install -e ".[tests]"

    # execute the tests
    pytest -x tests


.. note:: regression test execution requires an internet connection