import logging
import os

import pytest
import sh

import core4.base
import core4.base.collection
import core4.config
import core4.config.tag
import core4.error
import core4.logger.mixin
import core4.service.operation
import core4.service.project
import core4.service.setup
import core4.util

curr_dir = os.path.abspath(os.curdir)

ASSET_FOLDER = '../asset'

def asset(*filename, exists=True):
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, ASSET_FOLDER, *filename)
    if not exists or os.path.exists(filename):
        return filename
    raise FileNotFoundError(filename)

@pytest.fixture(autouse=True)
def reset(tmpdir):
    logging.shutdown()
    # logging mixin (setup complete)
    core4.logger.mixin.CoreLoggerMixin.completed = False
    # setup
    os.environ["CORE4_OPTION_folder__root"] = str(tmpdir)
    os.environ["CORE4_CONFIG"] = asset("config/empty.yaml")
    core4.logger.mixin.logon()
    yield
    os.chdir(curr_dir)
    # run @once methods
    for i, j in core4.service.setup.CoreSetup.__dict__.items():
        if callable(j):
            if "has_run" in j.__dict__:
                j.has_run = False
    # singletons
    core4.util.tool.Singleton._instances = {}
    # os environment
    dels = []
    for k in os.environ:
        if k.startswith('CORE4_'):
            dels.append(k)
    for k in dels:
        del os.environ[k]

def origin():
    origin = os.path.abspath(
        os.path.join(core4.base.main.CoreBase.project_path(), ".."))
    return origin

def test_quick(tmpdir):
    os.chdir(tmpdir.strpath)
    core4.service.project.make_project("test_project", "test project",
                                       auto=True, origin=origin())


def test_create(tmpdir):
    os.chdir(tmpdir.strpath)
    core4.service.project.make_project("test_project", "test project",
                                       auto=True, origin=origin())
    os.chdir(os.path.join(tmpdir.strpath, "test_project"))
    out = sh.git(["status"])

    assert "On branch master" in out
    assert "Your branch is up-to-date with 'origin/master'" in out
    assert "nothing to commit" in out

    os.chdir(tmpdir.strpath)
    core4.service.project.make_project("test_project", "test project",
                                       auto=True)

    with pytest.raises(SystemExit):
        core4.service.project.make_project("test-project", "test project",
                                           auto=True)


def test_build(tmpdir):
    os.chdir(tmpdir.strpath)
    core4.service.project.make_project("test_project", "test project",
                                       auto=True)
    os.chdir(os.path.join(tmpdir.strpath, "test_project"))
    # not develop
    with pytest.raises(SystemExit) as code:
        core4.service.operation.build()
    assert code.type == SystemExit
    assert code.value.code == 3
    # no changes
    sh.git(["checkout", "develop"])
    with pytest.raises(SystemExit) as code:
        core4.service.operation.build()
    assert code.type == SystemExit
    assert code.value.code == 5
    # not clean
    fh = open(os.path.join(tmpdir.strpath, "test_project", "README.md"), "a")
    fh.write("some change")
    fh.close()
    with pytest.raises(SystemExit) as code:
        core4.service.operation.build()
    assert code.type == SystemExit
    assert code.value.code == 4

    sh.git(["commit", ".", "-m", "second commit"])

    # version mismatch
    with pytest.raises(SystemExit) as code:
        core4.service.operation.build(0, 0, 0)
    assert code.type == SystemExit
    assert code.value.code == 6
    # success
    core4.service.operation.build(0, 0, 1)
    # check release
    out = sh.git(["branch", "-a"])
    "* release-0.0.2" in out
    "remotes/origin/release-0.0.2" in out


def test_release(tmpdir):
    os.chdir(tmpdir.strpath)
    core4.service.project.make_project("test_project", "test project",
                                       auto=True)
    os.chdir(os.path.join(tmpdir.strpath, "test_project"))
    sh.git(["checkout", "develop"])
    fh = open(os.path.join(tmpdir.strpath, "test_project", "README.md"), "a")
    fh.write("some change")
    fh.close()
    sh.git(["commit", ".", "-m", "second commit"])

    core4.service.operation.build(0, 0, 2)

    # wrong branch (master)
    with pytest.raises(SystemExit) as code:
        core4.service.operation.release()
    assert code.type == SystemExit
    assert code.value.code == 3

    sh.git(["checkout", "master"])

    with pytest.raises(SystemExit) as code:
        core4.service.operation.release()
    assert code.type == SystemExit
    assert code.value.code == 7

    sh.git(["merge", "release-0.0.2"])

    with pytest.raises(SystemExit) as code:
        core4.service.operation.release()
    assert code.type == SystemExit
    assert code.value.code == 7

    sh.git(["checkout", "develop"])
    sh.git(["merge", "release-0.0.2"])

    # wrong branch (master)
    with pytest.raises(SystemExit) as code:
        core4.service.operation.release()
    assert code.type == SystemExit
    assert code.value.code == 3

    sh.git(["checkout", "master"])
    core4.service.operation.release()

    assert sh.git(["tag"]).strip() == "0.0.2"

