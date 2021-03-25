.. _deploy:

########################
build and rollout system
########################


build a new release
###################

core4's main objective is the simplification of the data scientists' and data
engineers' life. For this reason core4 helper tools facilitate the build,
release and deployment process (see :doc:`tools`). Even though you can execute
these activities with manual steps and best practices the tools streamline the
workflow and improve time-to-market of new features and bug fixes.

Following the git branching model structured by Vincent Driessen
(see https://nvie.com/posts/a-successful-git-branching-model/) each core4
project is supposed to have at least the branches ``master`` and ``develop``

All projects initialised with ``coco --init`` carry these two branches by
default.

We consider origin/master to be the main branch where the source code of HEAD
always reflects a production-ready state. Branch origin/develop is the main
branch where the source code of HEAD always reflects a state with the latest
delivered development changes for the next release.

When the source code in the develop branch reaches a stable point and is ready
to be released, all of the changes should be merged back into master somehow
and then tagged with a release number.

This is done with the support of core4 tool ``coco`` as follows.

Suppose you have implemented your changes in a dedicated branch named
``mra.doc``. To build a new release you first have to merge this branch into
``develop`` to reflect you latest development changes::

    git checkout develop
    git merge mra.doc


Build a new release with::

    coco --build


If your working tree is clean and no pending release exists, this creates a new
release branch with the specified release number.

You can continue to push any additional changes into this release branch. Just
consider the git workflow of Vincent Driessen to add bug fixes to this branch
but no new features. They must be merged into develop, and therefore, wait for
the next big release.

When you are happy with your release branch to be rolled out, checkout branch
develop to merge back the release. Do the same with branch ``master``::

    # merge into develop
    git checkout develop
    git merge release-*

    # merge into master
    git checkout master
    git merge develop


Now is the time to finalize the release with:

    coco --release


``coco`` verifies that your working tree is clean and that the pending release
has been merged into branches ``develop`` and ``master``. If all validations
succeed, then a tag reflecting the release number is created and pushed to
origin. The release branch is now obsolete and automatically removed from the
local and remote repository.


.. note:: This build and release workflow applies to core4 projects as well as
          to the core4 framework itself.


``coco --dist`` is a utility command to build all webapps. Web applications are
identified with a ``package.json`` file in their base folder. If this file
contains the following attributes, the ``--dist`` option executes the specified
build commands and includes the ``./dist`` directory into the ``MANIFEST.in``
file.