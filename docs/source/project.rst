.. _project:

#################
project structure
#################

core4 is a framework. A core4 project uses the framework. From a business
perspective a project encapsulates non-related projects, products, business
domains or tenants.

From a technical perspective a core4 project is a Python package which imports
core4 functionalities and is marked as a core4 project with version, build and
title information and an optional project description.

A core4 project package named ``my_project`` for example follows the folder
structure::

    my_project             ... repository root
     |- my_project         ... package root
     |  |- __init__.py    ... project main Python file carrying project meta data
     |  '- my_project.yaml ... project configuraiton file
     |- tests             ... project unit tests
     |- requirements.txt  ... project requirements
     |- README.md         ... project long description
     '- setup.py          ... project setup file



There are some helper tools available to support project management. These
are:

* ``coco --project`` to create a new project, see :ref:`project_creation`
* ``coco --build`` to package a project ready for deployment, see
  :ref:`project_build`
* ``cadrin --deploy <project>`` to deploy a project to a runtime environment,
  see :doc:`deploy`
* ``coco --maintenance <project>`` to enter maintenance mode for all jobs
  of a project, see :ref:`project_maintenance`.


technical details
=================

From a technical perspective there are three aspects which require further
details. This is how core4 identifies its projects, the project creation
mechanic and the repository where projects reside.

Let's start with project creation.


.. _project_creation:

project creation
----------------

Use :ref:`coco <coco>` to create a new project. The project will be created
in the current working directory::

    coco --project my_project

This will inquire further informaiton from the user and after some confirmation
create the project in the current working directory.

You can also leave out the project name (``my_project`` in the example). With no
project name specified, :ref:`coco` will inquire *all* information
inateractively::

    coco --project

    core4 project creation
    ======================
    Name: my_project
    Description: This is a simple test project

    type [yes] to continue or press CTRL+C: yes

    created my_project/my_project/__init__.py
    created my_project/my_project/my_project.yaml
    created my_project/setup.py
    created my_project/requirements.txt
    created my_project/README.md
    created my_project/tests/__init__.py
    created my_project/.gitignore
    done.


The helper script has created all essential project files including the main
project module ``__init__.py``, the project configuration file
``my_project.yaml``, the ``setup.py``, ``requirements.txt`` and ``README.md``
file as well as an empty ``test`` suite. For your convinience a standard
``.gitignore`` file has been added, too.

After installation, e.g. with ``pip``, the project is installed. We highly
recommend to work inside your preferred python virtual environment::

    workon core4
    cd my_project
    pip install .


project repository location
---------------------------

For seamless deployment in any runtime environment the project needs to be
stored and synchronised with git versioning system.

For testing purposes you might want to create a local git repository and build
a release of your project::

    # create bare git repository in /tmp/my_project.git
    cd /tmp/
    git init --bare my_project.git

    # create new project in home directory
    cd
    coco --project

    > core4 project creation
    > =====================
    > Name: my_project
    > Description: my first project
    >
    > type [yes] to continue or press CTRL+C: yes
    >
    > created my_project/requirements.txt
    > created my_project/setup.py
    > created my_project/README.md
    > created my_project/.gitignore
    > created my_project/tests/__init__.py
    > created my_project/my_project/my_project.yaml
    > created my_project/my_project/__init__.py
    > done.

    cd my_project/
    # initialise my_project as a git working directory,
    git init
    # add, commit and push files
    git add .
    git commit -m "initial commit"
    git remote add origin file:///tmp/my_project.git
    git push -u origin master


.. _project_build:

build project release
---------------------

.. todo: continue with coco --build


.. _project_maintenance:

project maintenance
-------------------

.. todo: continue with project maintenance


project iteration
-----------------




