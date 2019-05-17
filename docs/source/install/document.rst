###################
documentation build
###################

Documentation requires the "tests" variant to setup::

    # clone core4
    git clone https://github.com/plan-net/core4.git

    # enter clone
    cd core4

    # create Python virtual environment
    python3 -m venv .venv

    # enter Python virtual environment
    source enter_env

    # install core4 in development mode
    pip install -e ".[tests]"

    # build documentation
    cd docs
    make html


The built HTML documentation is available in folder ``build/html/index.html``.
