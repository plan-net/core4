########################
quick installation guide
########################

This quick installation guide installs the prerequisites and uses the default
core4 settings. The setup has been tested with Debian 9 (Stretch). For Ubuntu
18.04 there is a dedicated :doc:`Ubuntu 18.04 quick install guide <ubuntu>`.


.. code-block:: shell
   :linenos:

    # install prerequisites
    sudo apt-get install python3-pip python3-venv python3-dev --yes
    sudo apt-get install gcc make git dirmngr libffi-dev --yes

    # install MongoDB
    sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 9DA31620334BD75D9DCB49F368818C72E52529D4
    echo "deb http://repo.mongodb.org/apt/debian "$(lsb_release -sc)"/mongodb-org/4.0 main" | sudo tee /etc/apt/sources.list.d/mongodb.list
    sudo apt-get update
    sudo apt-get install mongodb-org --yes
    sudo systemctl start mongod.service
    sudo systemctl enable mongod.service

    # clone core4
    git clone https://github.com/plan-net/core4.git

    # setup and enter Python virtual environment
    cd core4
    python3 -m venv .venv
    source enter_env

    # install core4 with webapps
    python setup.py --fe

    # finish local setup with MongoDB and local.yaml
    python local_setup.py


Test installation of the core4os backend by running the worker with::

    coco --worker


Open up another terminal, enter Python virtual environment, list available jobs
and enqueue the dummy job::

    source enter_env
    coco --job
    coco --enqueue core4.queue.helper.job.example.DummyJob


Use the job id to review job details::

    coco --detail <job_id>


Open up another terminal, enter Python virtual environment, and launch the
core4 api container::

   coco --app --filter core4.api.v1

Visit the app manager at http://0.0.0.0:5001 with username ``admin`` and
password ``admin``.


**What's next:**

* learn how to :doc:`develop` with core4os
* read about R setup and usage
* read about how to run core4os :doc:`test`
* read the :doc:`prereq` and learn how to :doc:`config <config>` the details of
  core4
* continue with :doc:`../example/index`
