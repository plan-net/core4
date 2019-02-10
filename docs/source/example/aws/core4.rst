########################################
setup core4 on Amazon Web Services (AWS)
########################################

The following shell protocol installs core4 framework
on Amazon Web Services (AWS). The protocol is based on a setup of Debian
GNU/Linux 9 (Stretch) on a *t3.micro* instance.

See also :doc:`mongodb`.

customise MongoDB IP address
----------------------------

The following shell variable will be used in the example. You will have to
update it to your ip address if you want to replicate this setup.

.. code-block:: shell

    export MONGODB="10.249.1.90"

update the system
-----------------

.. code-block:: shell

    sudo apt-get update --yes

install essentials
------------------

.. code-block:: shell

    sudo apt-get install python3-pip python3-venv git runit runit-systemd --yes

prepare directories
-------------------

.. code-block:: shell

    sudo mkdir /srv/core4
    sudo chown admin:root /srv/core4
    sudo chmod 755 /srv/core4

    sudo mkdir /srv/core4.prod
    sudo chmod 775 /srv/core4.prod
    sudo chown admin:root /srv/core4.prod

    sudo mkdir /etc/core4
    sudo chmod 750 /etc/core4
    sudo chown admin:root /etc/core4

install core4
-------------

.. code-block:: shell

    cd /srv/core4.prod

    #export LC_ALL=de_DE.UTF8
    ssh-keygen -R git.bi.plan-net.com
    ssh-keyscan git.bi.plan-net.com >> /home/admin/.ssh/known_hosts

    # requires private key id_rsa
    GIT_SSH_COMMAND='ssh -i /home/admin/.ssh/id_rsa' git clone ssh://mra@git.bi.plan-net.com/srv/git/core4.git

    cd core4
    git checkout master
    /usr/bin/python3 -m venv .venv

    # install core4
    /srv/core4.prod/core4/.venv/bin/pip install -U pip
    /srv/core4.prod/core4/.venv/bin/pip install -U .

core4 configuration
-------------------

.. code-block:: shell

    sudo tee /etc/core4/local.yaml <<EOF
    DEFAULT:
      mongo_url: mongodb://core:654321@$MONGODB:27017
      mongo_database: core4test

    # system folders
    folder:
      root: /srv/core4
      home: /srv/core4.prod

    # logging setup
    logging:
      stderr: INFO
      mongodb: INFO

    worker:
      min_free_ram: 64

    api:
      setting:
        cookie_secret: I would like to be a chicken
      port: 80
      admin_password: corevier
    EOF

test core4 setup
----------------

.. code-block:: shell

    /srv/core4.prod/core4/.venv/bin/coco --who

Expected output is something like this::

    USER:
      admin IN adm, dialout, cdrom, floppy, sudo, audio, dip, video, plugdev, netdev, admin
    UPTIME:
      0:11:27.594235 (688 sec.)
    PYTHON:
      /srv/core4.prod/core4/.venv/bin/python3 (3, 5, 3, 'final', 0)
    CONFIGURATION:
      file:///etc/core4/local.yaml
      file:///srv/core4.prod/core4/.venv/lib/python3.5/site-packages/core4/core4.yaml
    MONGODB:
      mongodb://core@10.249.1.90:27017/core4test
    DIRECTORIES:
      home:     /srv/core4.prod
      transfer: /srv/core4/transfer
      process:  /srv/core4/proc
      archive:  /srv/core4/arch
      temp:     /srv/core4/temp
    DAEMONS:
      none.

install project example mypro
-----------------------------

.. code-block:: shell

    cd /srv/core4.prod
    git clone https://github.com/m-rau/mypro.git
    cd mypro/
    python3 -m venv .venv
    .venv/bin/pip install -U pip
    GIT_SSH_COMMAND='ssh -i /home/admin/.ssh/id_rsa'  .venv/bin/pip install -U git+ssh://mra@git.bi.plan-net.com/srv/git/core4.git

daemonize worker
----------------

.. code-block:: shell

    sudo mkdir /etc/sv/core4
    sudo tee /etc/sv/core4/run <<EOF
    #!/bin/sh

    exec chpst -uadmin /srv/core4.prod/core4/.venv/bin/coco --worker
    EOF

    sudo chmod 755 /etc/sv/core4/run
    sudo ln -s /etc/sv/core4 /etc/service/core4

After a few seconds the runit supervisor should report success with:

.. code-block:: shell

    sudo sv status core4

The output should be something like this::

    run: core4: (pid 7832) 5s

test job execution
------------------

.. code-block:: shell

    /srv/core4.prod/core4/.venv/bin/coco -e core4.queue.helper.job.DummyJob sleep=30
    /srv/core4.prod/core4/.venv/bin/coco -e mypro.job.PrimeJob start=1 end=1000
    /srv/core4.prod/core4/.venv/bin/coco --info
    /srv/core4.prod/core4/.venv/bin/coco --listing
