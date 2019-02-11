################
regression tests
################

Regression tests require the "tests" variant to setup::

    # clone core4
    git clone ssh://git.bi.plan-net.com/srv/git/core4.git

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
