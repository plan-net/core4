##################
Ubuntu quick guide
##################

This quick installation guide installs the prerequisites and uses the default
core4 settings. The setup has been tested with Ubuntu 18.04. For Debian 9 there
is a dedicated :doc:`quick install guide <quick>`.


.. code-block:: shell
   :linenos:

   # install prerequisites
   sudo apt install python3-pip python3-venv python3-dev --yes
   sudo apt install gcc make git dirmngr libffi-dev --yes
   sudo apt install mongodb --yes  # install MongoDB 3.6

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


Test installation of the core4os backend by running the worker with::

    coco --worker


Open up another terminal, enter Python virtual environment, list available jobs
and enqueue the dummy job::

    source enter_env
    coco --job
    coco --enqueue core4.queue.helper.job.example.DummyJob


Use the job id to review job details::

    coco --detail <job_id>
