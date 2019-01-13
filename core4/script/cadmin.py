"""
cadmin - core4 administration utililty.

deploy project in prod
    upgrade project, core4 and packages

    cadmin --install mypro==1.2.3 --repository
    cadmin --upgrade

    export CORE4_HOME=/tmp/core4.home
    export CORE4_REPOSITORY=ssh://git.bi.plan-net.com/srv/git/core4.git
    export CORE4_PROJECT=core4
    export CORE4_PROJECT_REPOSITORY=file:///home/mra/core4.dev/mypro/.repos

    # core4
    # -------------------------------------------------------------------------
    cd $CORE4_HOME
    mkdir $CORE4_PROJECT
    cd $CORE4_PROJECT
    python3 -m venv .venv
    . .venv/bin/activate
    pip install -U git+$CORE4_REPOSITORY

    # here: install local.yaml
    mkdir ~/.core4
    nano ~/.core4/local.yaml

        DEFAULT:
          mongo_url: mongodb://core:654321@localhost:27017
          mongo_database: core4dev

        folder:
          home: /tmp/core4.home

        logging:
          mongodb: INFO

        worker:
          min_free_ram: 16

        api:
          setting:
            cookie_secret: hello world
          token:
            secret: hello world again

        core4_origin: git+ssh://git.bi.plan-net.com/srv/git/core4.git

    # test job success
    deactivate

    # mypro
    # -------------------------------------------------------------------------

    export CORE4_PROJECT=mypro
    export CORE4_PROJECT_REPOSITORY=file:///home/mra/core4.dev/mypro/.repos

    cd $CORE4_HOME
    mkdir $CORE4_PROJECT
    cd $CORE4_PROJECT
    python3 -m venv .venv
    . .venv/bin/activate
    pip install -U git+$CORE4_REPOSITORY
    pip install -U git+$CORE4_PROJECT_REPOSITORY

    deactivate

    # upgrade mypro
    # -------------------------------------------------------------------------

    . .venv/bin/activate

    pip install -U git+$CORE4_REPOSITORY
    pip install -U git+$CORE4_PROJECT_REPOSITORY


    cd demo/voting/webapps/manager
    yarn
    yarn build
    cd ../voting
    yarn
    yarn build
    coco --app --filter demo.voting


develop project
    upgrade core4 and packages

    cadmin --develop mypro

develop core4
    upgrade packages

    cadmin --develop core4

develop project and core4 together
    upgrade packages

    cadmin --develop mypro


cadmin --upgrade --all


Usage:
  cadmin    --project
  cadmin    --version

Options:
  -h --help       Show this screen.
  -v --version    Show version.
"""

from docopt import docopt


def main():
    args = docopt(__doc__, help=True)
    if args["--project"]:
        pass
    else:
        raise SystemExit("nothing to do.")


if __name__ == '__main__':
    import sys

    sys.argv.append("--project")
    main()
