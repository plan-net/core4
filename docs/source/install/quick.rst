###########
quick guide
###########

This quick installation guide installs the prerequisites and uses the default
core4 settings. The setup has been tested with Debian 9 (Stretch). For Ubuntu
18.04 there is a dedicated :doc:`Ubuntu 18.04 quick install guide <ubuntu>`.


.. code-block:: shell
   :linenos:

   # install prerequisites
   sudo apt-get install python3-pip python3-venv python3-dev git dirmngr --yes

   # install MongoDB
   sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 9DA31620334BD75D9DCB49F368818C72E52529D4
   echo "deb http://repo.mongodb.org/apt/debian "$(lsb_release -sc)"/mongodb-org/4.0 main" | sudo tee /etc/apt/sources.list.d/mongodb.list
   sudo apt-get update
   sudo apt-get install mongodb-org --yes
   sudo systemctl start mongod.service
   sudo systemctl enable mongod.service

   # install nodejs and npm
   wget -qO- https://deb.nodesource.com/setup_11.x | sudo bash -
   sudo apt-get update
   sudo apt-get install -y nodejs

   # install yarn
   wget -qO- https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
   echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
   sudo apt-get update
   sudo apt-get install yarn --yes
   sudo npm -g install vue-cli


   # clone core4
   git clone https://github.com/plan-net/core4.git

   # setup and enter Python virtual environment
   cd core4
   python3 -m venv .venv
   source enter_env

   # install core4
   pip install --upgrade pip
   pip install .

   # finish local setup with MongoDB and local.yaml
   python local_setup.py

   # build core4 web apps
   cadmin build


Revisit your core4 settings with::

    coco --who


Start a core4 worker with::

    coco --worker


In a second console start core4 application server with::

    coco --app


Visit the core4 landing page, look around at http://`hostname`:5001 and start a
job in a third console with::

    coco --enqueue core4.queue.helper.job.example.DummyJob sleep=30


**What's next:**

* read the full installation guide and learn how to configure the details of
  core4
* learn how to :doc:`develop`
* continue with :doc:`../example/index`
