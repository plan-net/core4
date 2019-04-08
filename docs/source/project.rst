.. _project:

#################
project structure
#################

core4 is a framework. core4 projects use the framework. From a business
perspective each project encapsulates related activities, products, business
domains or tenants. From a technical perspective a core4 project is a Python
package with its own Python virtual environment. It uses core4 functionalities
and is marked as a core4 project with version, build, title information and an
optional project description.

A core4 project package named ``project1`` for example has the following
folder structure::

    project1                 ... repository root
     |- .venv                ... Python virtual environment directory
     |- .repos               ... bare git repository controlling the project
     |- requirements.txt     ... requirements build from ``pip freeze``
     |- tests                ... unit tests
     |- README.md            ... long description
     |- setup.py             ... setup file
     |- enter_env            ... shell script to enter the project environment
     '- project1             ... project root
        |- __init__.py       ... main Python file carrying project meta data
        '- project1.yaml     ... configuraiton file


Helper tools support project management:

* ``coco --init`` to create a new project
* ``coco --build`` to prepare a new project release
* ``coco --release`` to finalise an existing project release
* ``cadmin --install`` and ``cadmin --upgrade`` to deploy a project to a
  runtime environment, see :doc:`deploy`


technical details
=================

From a technical perspective there are several aspects which require further
attention. This is how core4 identifies its projects, the project creation
mechanics and the repository where projects reside.

Let's start with project creation.


.. _project_creation:

project creation
----------------

Use ``coco --init`` to create a new project. The project will be
created in the current working directory.

This will inquire further information from the user and after some confirmation
the helper script creates the project in the current working directory.

The helper script creates all essential project files as describe above
(see :ref:`project`).


project repository location
---------------------------

For seamless deployment in any runtime environment the project needs to be
stored and synchronised with git versioning system. :ref:`project_creation`
automatically creates a bare git repository. This repository is linked to your
project sources.

This repository carries an initial commit, a branch ``master`` and a branch
``develop``.

To share this git repository with other users you have to manually synchronise
this bare repository with a git repository accessible by your team.
Alternatively move the bare repository to a public or private git server. Once
this has been done, you can update your remote origin with the following git
command and remove the bare repository in ``.repos`` from the project sources::

    git remote set-url origin git://new.url.here
    rm -Rf .repos


See also :doc:`deploy` and :doc:`tools`.
