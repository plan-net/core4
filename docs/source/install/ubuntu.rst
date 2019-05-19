##################
Ubuntu quick guide
##################

This quick installation guide installs the prerequisites and uses the default
core4 settings. The setup has been tested with Ubuntu 18.04. For Debian 9 there
is a dedicated :doc:`quick install guide <quick>`.


.. code-block:: shell
   :linenos:

   # install prerequisites
   sudo apt install python3-pip python3-venv --yes
   sudo apt install git --yes
   sudo apt install mongodb --yes

   # install yarn/vue-cli
   wget -qO- https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
   echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
   sudo apt update
   sudo apt install yarn --yes
   sudo yarn global add @vue/cli

   # clone core4
   git clone https://github.com/plan-net/core4.git
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

    coco -enqueue core4.queue.helper.job.example.DummyJob sleep=30
