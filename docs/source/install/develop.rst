#############################################
develop and maintain core4 and core4 projects
#############################################

In this tutorial you will learn how to create a new
:ref:`core4os project <project>` and how to develop a simple job. All examples
assume that you have installed and setup core4os framework as described in
the :doc:`quick`.


project initiation
==================

A core4os project is a repository with a dedicated Python virtual environment.
Use command ``coco --init`` to create a new project. To do so, you first need to
enter an existing core4os Python virtual environment. In this tutorial we will
use the core4os repository which has been cloned and installed in the
:doc:`quick`. Open up a shell and execute the following commands to enter this
environment::

    # enter core4os directory
    cd ~/core4

    # enter Python virtual environment
    source enter_env


You are now in a core4 environment and can create a new project using the
core4os ``coco --init`` command.

Enter the directory where your new project is to be located::

    # enter your home directory
    cd

Choose a project name *"mypro"* and create your project with::

    coco --init mypro "My first core4 project"


After your confirmation by typing ``yes`` this will:

# create a project directory ``./mypro``
# create a Python 3 virtual environment at ``./mypro/.venv``
# create a bare git repository at ``./mypro/.repos`` with an initial commit and
  two branches, ``master`` and ``develop``


Now exit the Python virtual environment you used to create the project and enter
the Python virtual environment we have just created inside ``~/mypro/.venv``::

    # leave core4os Python environment
    deactivate
    # enter project repository
    cd mypro
    # activate mypro's Python virtual environment
    source enter_env


The repository contains the following directory and main files::

    .
    ├── .repos            # bare git repository for your project
    ├── .git              # git working directory
    ├── .gitignore        # files to be ignored by git
    ├── .venv             # Python virtual environment
    ├── enter_env         # use to enter the Python virtual environment
    ├── MANIFEST.in       # Python MANIFEST package file
    ├── mypro             # mypro package root
    │   ├── __init__.py   # mypro package file
    │   └── mypro.yaml    # mypro configuration file
    ├── README.md         # quick introduction to mypro project
    ├── requirements.txt  # empty dependencies file
    ├── setup.py          # Python setup file
    └── tests             # Python test package root
        └── __init__.py   # Python test package file


In ``mypro/.repos`` resides the git repository. Directory ``mypro/.git``
contains your git local working tree. The Python virtual environment is in
``mypro/.venv``.

These directories are only created if they do not exist and your
working tree is not connected to a remote git repository. In this case, ``.git``
carries the connection to the remote repository and .repos does not exist.


job development
===============

Let's create our own test job. Switch to the git develop branch following the
`gitflow`_::

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


Save and close the file. Directly execute the job by starting ``myjob.py`` as
in::

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

   * one for core4,
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
