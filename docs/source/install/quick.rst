###########
quick guide
###########

This quick installation guide installs the prerequisites and uses the default
core4 settings.

.. code-block:: shell
   :linenos:

    # install prerequisites
    apt-get install python3-pip python3-venv git python3-dev mongodb

    # clone core4
    git clone https://github.com/plan-net/core4.git

    # setup and enter Python virtual environment
    cd core4
    python3 -m venv .venv
    source enter_env

    # install core4
    pip install -U pip
    pip install .


Revisit your core4 settings with::

    coco -who


Start a core4 worker with::

    coco --worker


In a second console start core4 application server with::

    coco --app


Visit the core4 landing page, look around at http://`hostname`:5001 and start a
job in a third console with::

    coco -enqueue core4.queue.helper.job.example.DummyJob sleep=30


**What's next:**

* read the full installation guide and learn how to configure the details of
  core4
* learn how to :doc:`develop`
* continue with :doc:`../example/index`

