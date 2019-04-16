.. _access:

###################################################
authentication, authorisation and access management
###################################################

core4 provides a simple authentication, authorization and access permission
scheme managed by the core4 API request handlers :class:`.LoginHandler`,
and :class:`.RoleHandler`.

Both classes are delivered through the :class:`.CoreApiServer'. The
:class:`.RoleHandler` is reserved for core4 administrators AKA *COPs*.

*COPs* can grant access to jobs, API requests, and databases. Additionally
application keys can be defined to customise specific access permissions, e.g.
for frontend features.


The structure of the permission scheme for jobs is::

    job://[qual_name]/[rx]

The ``qual_name`` variable is parsed as a regular expression. The ``r``
modifier grants read permissions. The user can read-only access all jobs
attributes for jobs matching the ``qual_name``. The ``x`` modifier grants
execution permissions. The user can enqueue, restart, remove and kill all jobs
matching the ``qual_name``.

These permissions are automatically verified when the user interacts with all
API request handlers in ``core4.api.v1.request.queue``


The structure of the permission scheme for API requests is::

    api://[qual_name]

The ``qual_name`` variable again is parsed as a regular expression matching
the *qualified name* of the API.

All users which are to be allowed to manage the ``DummyJob`` at *qual_name*
``core4.queue.helper.job.example.DummyJob`` require the following permissions
depending on the exact intended grants::

    api://core4.api.v1.request.queue.job.JobHandler
    api://core4.api.v1.request.queue.job.JobPost
    api://core4.api.v1.request.queue.job.JobStream
    api://core4.api.v1.request.queue.state.QueueHandler
    job://core4.queue.helper.job.example.DummyJob/x

More efficiently the permission scheme can be expressed as::

    api://core4.api.v1.request.queue.*
    job://core4.queue.helper.job.example.*/x

These permissions are automatically verified when the user interacts with the
API request handlers in ``core4.api.v1.request``


The structure of the permission scheme for MongoDB database access is::

    mongodb://[database]

Please note that the database specification requires an exact match. No
patterns or regular expressions are allowed, here. The permission scheme only
supports read-only database access. Additional requirements cannot be defined
with core4. These special access rights have to be managed outside of the
core4 framework. To grant read-only access to the default core4 system database
a user requires the following permission::

    mongodb://core4


The structure of the permission scheme for custom application keys is::

    app://[key]

These keys provide a means to define custom permission settings managed by
core4 jobs or the core4 API. We have for example used these keys to provide
a user/role based regional authorization scheme::

    app://reporting/eu/de/by

Users with a application key ``reporting`` have access to all regions. Users
with an application key ``reporting/eu`` have access to european data. Users
with an application key ``reporting/eu/de`` have access to german data, etc.

Please note that these custom application keys have to be controlled by the
:class:`.CoreJob` or :class:`.CoreRequestHandler`.


default user
============

The core4 API ships with a default administrator specified by the following
core4 configuration keys:

* ``api.admin_username``
* ``api.admin_realname``
* ``api.admin_password``

The password is not defined by default and you will have to specifiy it in your
local settings to be able to launch any application container::

    user_rolename: standard_user
    user_realname: standard user group
    user_permission:


default role
============

The core4 API ships with a default user role. This user role should be assigned
to all users as it specifies the minimum access permissions. The default user
role as specified with the following core4 configuration keys:

* ``api.user_rolename`` - the name of the default role
* ``api.user_realname`` - the real name of the default role
* ``api.user_permission`` - list of default permissions

The default settings of this role are::

  user_rolename: standard_user
  user_realname: standard user group
  user_permission:
    - api://core4.api.v1.request.standard.*


.. note:: The default role is not automatically assigned to new roles and
          users. It must be explicitely assigned at user creation. See the
          example below.


example::

    from requests import post
    url = "http://localhost:5001/core4/api/v1"
    rv = post(url + "/roles",
              json={
                  "name": "reporting",
                  "realname": "Reporting User",
                  "role": [
                    "standard_user"
                  ],
                  "perm": [
                    "api://reporting.api.v1.public"
                  ]
              },
              auth=("admin", "hans")
