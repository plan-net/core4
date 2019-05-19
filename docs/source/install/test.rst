################
regression tests
################

Regression tests require the "tests" variant to setup and a MongoDB service
listening to hostname ``testmongo``. Add the following line to your
``/etc/hosts`` file if your test MongoDB instance is installed on your local
host::

    127.0.0.1       testmongo


Install core4 and execute the regression tests with the following shell
commands::

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