"""
cadmin - core4 administration utililty.

deploy project in prod
    upgrade project, core4 and packages

    cadmin --install mypro==1.2.3 --repository
    cadmin --upgrade

    export CORE4_HOME=/tmp/core4.home
    export CORE4_PROJECT=core4
    export CORE4_PROJECT_BRANCH=mra.ops
    export CORE4_REPOSITORY=ssh://git.bi.plan-net.com/srv/git/core4.git

    SETUP

        cd $CORE4_HOME
        mkdir $CORE4_PROJECT
        cd $CORE4_PROJECT
        python3 -m venv .venv
        . .venv/bin/activate
        git clone git+$CORE4_REPOSITORY .repos
        cd .repos
        git checkout $BRANCH
        pip install .
        cd ..
        rm -Rf .repos

    UPGRADE

        cd $CORE4_HOME
        pip install

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
