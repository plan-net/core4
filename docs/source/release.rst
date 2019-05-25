#################################
release management and deployment
#################################

core4 applies the same mechanics of release management and deployment/rollout
for all *core4 projects* as well as for *core4 itself*. Even though the tools
and mechanics are the same, the process and steps involved may vary. The
rigidity, quality management control, deployment and go-live for an individual
project depend on the specific needs, the business criticality and hence
nature of the project.

The scope of this section is to outline and describe the release management
and deployment process applied to core4. You might use it as a blueprint for
other core4 *projects*. Yet we strongly advise to carefully analyse the
requirements of each project *before* rollout and to make an informed decision
if you create alternatives or shortcuts. core4 considers itself as an agile
data integration, execution automation and smart insight apps architecture.
Nevertheless you have to consciously manage core4 operations dependening on the
implementation, build, test, release and deployment activities and processes.
Anticipate your requirements and forthcoming scenarios.

releated documents
==================

* :doc:`deploy`
* :doc:`project`
* :doc:`roadmap`
* :doc:`tools`


release principles and concepts
===============================

The following release principles and mechanics are inspired by
`Vincent Driessen's GitFlow inspiring insights about a prop git branching model
<https://nvie.com/posts/a-successful-git-branching-model/>`_.


master branch
-------------

Git branch origin/master is the main branch where the source code of HEAD
always reflects a production-ready state. Each time when changes go into
master, this is a new production release by definition.

Only members of the *core4 maintainer* team are allowed to push changes to
*master*. The maintainers must use ``coco --release`` command to push changes.
This associates the change commit with a new release number (see :ref:`coco`).

develop branch
--------------

Git branch origin/develop is where the source code of HEAD reflects a state
with the latest delivered development changes for the next release. This is
where continuous regression tests are executed.

Only members of the *core4 developer* team are allowed to push changes to
*develop*. All other contributors are supposed to fork the core4 source code
and execute *pull requests* to the maintainers. See ``CONTRIBUTING.md``
document in the source code tree.

feature branches
----------------

Git feature branches are used to develop new features for the upcoming or a
distant future release. When starting development of a feature, the target
release in which this feature will be incorporated may well be unknown at that
point. The feature branch exists as long as the feature is in development, but
will eventually be merged back into develop or discarded.

Feature branches typically exist in developer repos only, not in origin.

release planning and the release branch
---------------------------------------

The developers and maintainers retain the :doc:`roadmap`. With the decision for
a new release, a new release branch is created from *develop* using
``coco --build``. Only members of the development team are allowed to create
a release branch. New features and fixes are still supposed to first go into
the *develop* branch and are merged into the release branch by the maintainer
team.

Continuous regression tests are executed with the release branch.

An upcoming release is announced in :doc:`roadmap` and logged in
:doc:`history`.


versioning scheme
-----------------

The core system at Serviceplan/Plan.Net was first developed in 2014. Version 1
was a prototype for data integration and automation. Version 2 was the first
production version. Version 3 included the addition of a ReST API, front-end
applications and mini applications.

Core version 4 is the Python 3 ported version.

This version number *4* reflects the history of core. It started as a working
title and this number *4* is associated with the open source initiative inside
our organisation. Version *4* is not considered a part of the versioning
scheme.

Instead we work with the following scheme known as semantic versioning:

#. major number - increments reflect significant, possibly breaking changes and
   extensions
#. minor number - increments reflect minor and non-breaking changes
#. maintenance number - increments reflect bug fixes and improvements
