#############################################
develop and maintain core4 and core4 projects
#############################################

In this scenario we will install core4 in ``~/core4.dev``, create, setup, build
and release a core4 project called *mypro*.

Ensure all dependencies have been installed. This is Python 3.5, MongoDB, pip
and git.

Open up a shell and execute the following commands to install core4::

    # create core4 home of your projects
    mkdir ~/core4.dev
    cd ~/core4.dev

    # clone core4
    git clone ssh://git.bi.plan-net.com/srv/git/core4.git

    # enter clone
    cd core4

    # create Python virtual environment
    python3 -m venv .venv

    # enter Python virtual environment
    source enter_env

    # install core4 in development mode
    pip install -e ".[tests]"


You have now a core4 environment and can create and develop your project. Choose
project name *"mypro"* and create your test project with::

    cd ~/core4.dev
    coco --init mypro "My first core4 project"


This has created the followinhg project structure::

    mypro/
    ├── README.md
    ├── enter_env
    ├── setup.py
    ├── install_requires.txt
    ├── requirements.txt
    ├── mypro
    │   ├── __init__.py
    │   └── mypro.yaml
    └── tests


This represents the bare project directory structure. Hidden directories
``.git``, ``.repos``, and ``.venv`` are available, too.

In ``mypro/.repos`` resides the git repository. Directory ``mypro/.git``
contains your git local working tree. The Python virtual environment is in
``mypro/.venv``.

These directories are only created if they do not exist and your
worktree is not connected to a remove git repository. In this case, ``.git``
carries the connection to the remote repository and .repos does not exist.

Now is the time to create your local core4 configuration in
``~/.core4/local.yaml``. Open your favorite editor or IDE and paste the
following content into this file. Ensure the configuration key ``folder.home``
addresses the core4 home directory created above::

    DEFAULT:
      mongo_url: mongodb://core:654321@localhost:27017
      mongo_database: core4dev

    logging:
      mongodb: INFO
      stderr: DEBUG
      stdout: ~

    folder:
      home: /home/<username>/core4.dev

    worker:
      min_free_ram: 32


Since every project comes with it's own Python virtual environment you must
watch your context, e.g. with `coco --who`. Therefore, exit current environment
"core4" with::

    deactivate


Next, enter project "mypro" Python virtual environment::

    source mypro/enter_env


Start a worker with::

    coco --worker


Test to enqueue a simple default job. Open up another shell, enter the
environment for this shell and enqueue the DummyJob::

    # enter mypro environment (2nd shell)
    source core4.dev/mypro/enter_env

    # test enqueue
    coco --enqueue core4.queue.helper.job.example.DummyJob


After successful execution show the job details from ``sys.queue`` and halt the
worker.

    # show details
    coco --detail <job-id>

    # stop the worker
    coco --halt


Now development. Let's create our own test job. Switch to the git develop
branch following the `gitflow`_::

    git checkout develop
    touch mypro/myjob.py


and paste the following snippet into the body of ``myjob.py``::

    import core4.queue.job
    import time


    class MyJob(core4.queue.job.CoreJob):
        author = "mra"
        schedule = "* * * * *"

        def execute(self, **kwargs):
            self.logger.info("hello world")
            for i in range(0, 10):
                time.sleep(1)
                self.progress(i / 10.)
                print("loop interval", i)


    if __name__ == '__main__':
        from core4.queue.helper.functool import execute
        execute(MyJob)


Save and close the file. Your development project should now look like this::

    mypro/
    ├── README.md
    ├── enter_env
    ├── setup.py
    ├── install_requires.txt
    ├── requirements.txt
    ├── mypro
    │   ├── __init__.py
    │   ├── mypro.py            # new file
    │   └── mypro.yaml
    └── tests


Directly execute the job by starting ``myjob.py`` as in::

    python mypro/myjob.py


Develop with your favorite IDE. Do not forget to address the correct Python
executable from ``.venv/bin/python`` and correct settings in ``local.yaml``.

Running a background worker allows direct use of the execution framework
addressing the job with its fully qualified name ``mypro.myjob.MyJob``::

    coco --enqueue mypro.myjob.MyJob


Now that we are happy with the job, let's build a release. We simulate the
typical deployment workflow for new features and bug fixing::

    # use develop branch for further development
    git checkout develop

    # add myjob.py
    git add .

    # commit all changes
    git commit . -m "first job"

    # build release 0.0.2
    coco --build


Finalize the release and merge branch *release-0.0.2* into branches develop and
master::

    # merge release into develop
    git checkout develop
    git merge release-0.0.2

    # merge release into master
    git checkout master
    git merge release-0.0.2

    # publish the release
    coco --release


This rather long and at first sight complicated workflow is straight forward if
you follow the `gitflow`_ concept. As a recap this summary outlines the most
relevant steps of this guideline so far.

#. Create home for core4 source and projects.

#. Manage multiple dedicated Python virtual environments.

   * One for core4,
   * one for each project.
   * Use ``coco --init`` as the helper tool to initialise the environment.
   * Enter and develop in project virtual environments.

#. Manage your ``local.yaml`` for MongoDB connection, logging and core4 project
   residence.

#. Develop with your favorite IDE, execute, and enqueue start jobs.

   * Use the git branching feature.
   * Push your changes into the develop branch.

#. Align and build new release with ``coco --build``.

#. After successful tests & QA merge your source changes from *release-0.0.2*
   to branches develop and master and finally rollout the release with
   ``coco --release``.

.. _gitflow: https://nvie.com/posts/a-successful-git-branching-model/
