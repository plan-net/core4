.. _plugin:

###################
plugin architecture
###################

core4 is a plugin based framework. From a business perspective a plugin
encapsulates non-related projects, products, business domains or tenants.

From a technical perspective a plugin is a Python package which imports core4
functionalities and is marked as a core4 plugin with version, build and title
information and an optional project description.

A core4 plugin package named ``my_plugin`` for example follows the folder
structure::

    my_plugin             ... repository root
     |- my_plugin         ... package root
     |  |- __init__.py    ... plugin main Python file carrying plugin meta data
     |  '- my_plugin.yaml ... plugin configuraiton file
     |- tests             ... plugin unit tests
     |- requirements.txt  ... plugin requirements
     |- README.md         ... plugin long description
     '- setup.py          ... plugin setup file



There are some helper tools available to support plugin management. These
are:

* ``coco --plugin`` to create a new plugin, see :ref:`plugin_creation`
* ``coco --build`` to package a plugin ready for deployment, see
  :ref:`plugin_build`
* ``cadrin --deploy <PLUGIN>`` to deploy a plugin to a runtime environment,
  see :doc:`deploy`
* ``coco --maintenance <PLUGIN>`` to enter maintenance mode for all jobs
  of a plugin, see :ref:`plugin_maintenance`.


technical details
=================

From a technical perspective there are three aspects which require further
details. This is how core4 identifies its plugins, the plugin creation
mechanic and the repository where plugins reside.

Let's start with plugin creation.


.. _plugin_creation:

plugin creation
---------------

Use :ref:`coco <coco>` to create a new plugin. The plugin will be created
in the current working directory::

    coco --plugin my_plugin

This will inquire further informaiton from the user and after some confirmation
create the plugin in the current working directory.

You can also leave out the plugin name (``my_plugin`` in the example). With no
plugin name specified, :ref:`coco` will inquire *all* information
inateractively::

    coco --plugin

    core4 plugin creation
    =====================
    Name: my_plugin
    Description: This is a simple test plugin

    type [yes] to continue or press CTRL+C: yes

    created my_plugin/my_plugin/__init__.py
    created my_plugin/my_plugin/my_plugin.yaml
    created my_plugin/setup.py
    created my_plugin/requirements.txt
    created my_plugin/README.md
    created my_plugin/tests/__init__.py
    created my_plugin/.gitignore
    done.


The helper script has created all essential plugin files including the main
plugin module ``__init__.py``, the plugin configuration file
``my_plugin.yaml``, the ``setup.py``, ``requirements.txt`` and ``README.md``
file as well as an empty ``test`` suite. For your convinience a standard
``.gitignore`` file has been added, too.

After installation, e.g. with ``pip``, the plugin is installed. We highly
recommend to work inside your preferred python virtual environment::

    workon core4
    cd my_plugin
    pip install .


plugin repository location
--------------------------

For seamless deployment in any runtime environment the plugin needs to be
stored and synchronised with git versioning system.

For testing purposes you might want to create a local git repository and build
a release of your plugin::

    # create bare git repository in /tmp/my_plugin.git
    cd /tmp/
    git init --bare my_plugin.git

    # create new plugin in home directory
    cd
    coco --plugin

    > core4 plugin creation
    > =====================
    > Name: my_plugin
    > Description: my first plugin
    >
    > type [yes] to continue or press CTRL+C: yes
    >
    > created my_plugin/requirements.txt
    > created my_plugin/setup.py
    > created my_plugin/README.md
    > created my_plugin/.gitignore
    > created my_plugin/tests/__init__.py
    > created my_plugin/my_plugin/my_plugin.yaml
    > created my_plugin/my_plugin/__init__.py
    > done.

    cd my_plugin/
    # initialise my_plugin as a git working directory,
    git init
    # add, commit and push files
    git add .
    git commit -m "initial commit"
    git remote add origin file:///tmp/my_plugin.git
    git push -u origin master


.. _plugin_build:

build plugin release
--------------------

.. todo: continue with coco --build


.. _plugin_maintenance:

plugin maintenance
------------------

.. todo: continue with plugin maintenance


plugin iteration
----------------




