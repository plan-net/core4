how to work with multiple core4 configuration
=============================================

The most simple approach to work with multiple core4 environments is to address
different core4 configuration YAML files with the environment variable
``CORE4_CONFIG``. If you have for example a configuration file
``~/,core4/local.yaml`` for development and another ``~/.core4/prod.yaml`` with
read-only connections to your production databases, then swith configuration
with::

    $ CORE4_CONFIG=~/.core4/local.yaml coco listing

or

    $ export CORE4_CONFIG=~/.core4/local.yaml
    $ coco listing

and

    $ CORE4_CONFIG=~/.core4/prod.yaml coco listing

or

    $ export CORE4_CONFIG=~/.core4/prod.yaml
    $ coco listing
