#######################
delivering static files
#######################

Delivering static files is supported by core4 with
:class:`.CoreStaticFileHandler`. The following example demonstrates the
publication of a private sphinx documentation site granting access to selected
roles.

The example starts from scratch with the setup of a new core4 project. If you
know how to setup a new core4 project continue with xxxxxx.


project setup
=============

Change to your favorite development folder, e.g. ``~/PycharmProjects`` and
setup the project with::

    coco --init home4 "core4 internal housekeeping project" --yes


This creates the following directory structure::

    .
    ├── enter_env
    ├── home4
    │   ├── home4.yaml
    │   └── __init__.py
    ├── MANIFEST.in
    ├── README.md
    ├── requirements.txt
    ├── setup.py
    └── tests
        └── __init__.py


sphinx setup
============

Enter the Python virtual environment, create a directory ``docs`` to host
your sphinx project and setup sphinx with::

    source home4/enter_env
    mkdir -p home4/docs
    cd home4/docs
    sphinx-quickstart


Answer a couple of questions and select the defaults if you are unsure. This
will create the following directory structure inside your ``./home4/docs``
folder::

    .
    ├── build
    ├── Makefile
    └── source
        ├── conf.py
        ├── index.rst
        ├── _static
        └── _templates


build documentation
===================

Let's build the documentation with::

    make html


implement document server
=========================

We will create a new ``.CoreApiContainer`` to deliver the built HTML documents.
Create the following directory inside the package directory
(``cd ../home4; mkdir -p home4/api/v1``)::

    home4
    ├── api
    │   └── v1
    ├── docs
    ├── home4.yaml
    └── __init__.py


Create a Python package and file ``server.py`` inside ``./home4/api/v1``
with the following commands::

    touch home4/api/__init__.py
    touch home4/api/v1/__init__.py
    touch home4/api/v1/server.py


Put the following code into ``server.py``:

.. code-block:: python

    from core4.api.v1.application import CoreApiContainer
    from core4.api.v1.request.static import CoreStaticFileHandler


    class DevopsManualServer(CoreApiContainer):
        rules = [
            (r'/devops', CoreStaticFileHandler, {
                "path": "/docs/build/html",
                "title": "devops manual",
                "protected": True
            }),
        ]


    if __name__ == '__main__':
        from core4.api.v1.tool.functool import serve
        serve(DevopsManualServer)


automated build with cadmin
===========================

We will use core4 deployment tool ``cadmin`` to automatically build this
documentation if an upgrade is available. See :ref:`cadmin`. This requires
a ``package.json`` inside ``home4/docs``::

    {
      "name": "devops-docs",
      "core4": {
        "build_command" : [
          "/usr/bin/python3 -m venv .venv_build",
          ".venv_build/bin/pip install sphinx sphinx-rtd-theme",
          "rm -Rf ./dist",
          ".venv_build/bin/sphinx-build -b html source build/html",
          "rm -Rf .venv_build"
        ],
        "dist": "./dist"
      }
    }




preparation
===========

First you will have to create two users.

.. code-block:: python

    from requests import post, get

    # login as admin
    login = get("http://devops:5001/core4/api/v1/login?username=admin&password=hans")
    token = login.json()["data"]["token"]
    # create user1
    rv = post("http://devops:5001/core4/api/v1/roles",
              headers={"Authorization": "Bearer " + token},
              json={
                  "name": "user1",
                  "realname": "Test User 1",
                  "email": "test1@plan-net.com",
                  "password": "very secret",
                  "role": ["standard_user"]
              })
    assert rv.status_code == 200
    # create user2
    rv = post("http://devops:5001/core4/api/v1/roles",
              headers={"Authorization": "Bearer " + token},
              json={
                  "name": "user2",
                  "realname": "Test User 2",
                  "email": "test2@plan-net.com",
                  "password": "very secret",
                  "role": ["standard_user"]
              })
    assert rv.status_code == 200


Verify both users exists with the role endpoint.

.. code-block:: python

    rv = get("http://devops:5001/core4/api/v1/roles",
              headers={"Authorization": "Bearer " + token})


To simulate a chat between both users, open two terminals and start the simple
terminal chat client script.

.. literalinclude:: chat.py


Before starting the script, ensure the :class:`.CoreApiServer` is up and
running with::

    cd core4
    source enter_env
    python core4/api/v1/server.py


In a second terminal, start the script for _user1_ with::

    cd docs/source/example
    python chat.py devops:5001 user1 "very secret"

In a third terminal, start the script for _user2_ with::

    cd docs/source/example
    python chat.py devops:5001 user2 "very secret"
