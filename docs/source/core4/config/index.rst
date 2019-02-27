######
config
######

Package :any:`core4.config <core4.config.main>` with class
:any:`core4.config.CoreConfig <core4.config.main.CoreConfig>` implement access
to core4 configuration data. core4 configuration delivers a configuration
system with the following features:

* YAML configuration syntax accessible with Python dict syntax and optional
  dot notation
* special YAML tags to simplify database access
* cascading configuration sources to customise existing configuration settings
  using configuration files, database collections and OS environment
* a clear seperation between core4 configuration and project specific settings
* default values


.. toctree::
   :caption: Table of Contents

   main
   tag
   map
   default


