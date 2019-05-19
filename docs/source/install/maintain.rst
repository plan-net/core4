############################################
develop and maintain existing core4 projects
############################################

In this scenario we will clone, setup, build and release the existing core4
project "mypro". This project has been created in the previous scenario under
``~/core4.dev/mypro``.

Open up a shell and execute the following commands to clone the project::

    # create a development folder
    mkdir ~/core4.dev

    # clone core4 project
    cd ~/core4.dev
    git clone file:///home/mra/core4.dev/mypro/.repos mypro

    # change to working tree
    cd mypro


This has created the following file/folder structure::

    mypro/
    ├── .git                    # created by git clone
    ├── README.md
    ├── enter_env
    ├── setup.py
    ├── install_requires.txt
    ├── requirements.txt
    ├── mypro
    │   ├── __init__.py
    │   └── mypro.yaml
    └── tests


Finally you must create a Python virtual environment, enter it and install
core4 inside this environment. It is recommended to install the project itself
in development mode::

    # create Python virtual environment
    python3 -m venv .venv

    # enter the environment
    source enter_env

    # install core4
    pip install -U git+https://github.com/plan-net/core4.git

    # install project mypro from current directory in development mode
    pip install -e .


Do not forget to have a global core4 configuration file at
``~/.core4/local.yaml``. See the example configuration yaml above.

To test the job mypro.myjob.MyJob execute the following commands in two
seperate shells::

    # Start worker in a shell
    coco --worker

    # Directly execute the job
    python mypro/myjob.py

    # enqueue job in another shell
    coco --enqueue mypro.myjob.MyJob

    # stop the worker
    coco --halt

