core4 setup
===========

You have multiple options to setup core:

#. in a development environment connecting to local and remote resources
#. in an operations environment connecting to remote production resources
#. in a production environment listening as a core worker

These environments are setup as Python virtual environments and you can run
all environments in parallel. Just watch your connection settings.

The following three sections describe in detail the steps required to setup
environments.

prerequisite
------------

Setup your Python virtual environment with Python 3.5 or higher using
virtualenvwrapper. Initialise your environments with::

    export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
    export WORKON_HOME=$HOME/.virtualenvs
    export PROJECT_HOME=$HOME/PycharmProjects
    source /usr/local/bin/virtualenvwrapper.sh

See http://virtualenvwrapper.readthedocs.io/en/latest/install.html on how to
setup virtualenvwrapper.


setup development environment
-----------------------------

Create Python virtual environment with::

    $ mkvirtualenv core4dev
    (core4dev) $ cd $PROJECT_HOME/core4
    (core4dev) $ pip install -r requirements.txt
    (core4dev) $ python tests/runner.py
    (core4dev) $ pip install -U -e .
    (core4dev) $ deactivate

Reactivate core4dev environment with `workon core4dev`.


