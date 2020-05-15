.. _access:

###################################################
authentication, authorisation and access management
###################################################

core4 provides a simple authentication, authorization and access permission
scheme managed by the core4 API request handlers :class:`.LoginHandler`,
and :class:`.RoleHandler`.

Both handlers are delivered through the :class:`.CoreApiServer'. The
:class:`.RoleHandler` is reserved for core4 administrators AKA *COPs*.

*COPs* can grant access to jobs, API requests, and databases. Additionally
application keys can be defined to customise specific access permissions, e.g.
for frontend features.

qualname
=========
All permissions, except the custom app:// permissions, used in core4 are based
on python's `qualname <https://www.python.org/dev/peps/pep-3155/>`_.

All classes and functions within python ship with a ``__qualname__`` attribute,
which contains a dotted path leading to the object from the module top-level.

core4 utilizes this qualname to assign permissions to an individual class within
a projects structure. This may be a job or an API endpoint.

Projects can easily be structured to depict its needed permission levels.
One usual approach is to utilize so called "subjects" that divide an application
into multiple logical blocks that require the same access permissions.
There might exist the following API structure for a web application::

    testproject/
    └── api
        └── v1
            ├── admin
            │   └── configuration.py
            ├── general
            │   ├── info.py
            │   └── welcome.py
            └── server.py


Within server.py one configures all URLs and their endpoints, this is required
when using core4os API features. The application is further devided into two
basic subjects: "admin" & "general". Both subjects can be easily obtained via
its qualname and are automatically usable within core4os permission management::

    # access to admin section
    api://testproject.api.v1.admin.*
    # access to general section
    api://testproject.api.v1.general.*

Please remember that a qualname does not necessarily reflect the URL that it
is mapped to. This is why all permissions are set in qualname notation (with
dots as separators, as opposed to the / used in URLs).

A possible frontend can access a user's permissions by utilizing the endpoint:
``<domain>/core4/api/v1/profile``

permission schemes
==================


job access
----------

The structure of the permission scheme **for jobs** is::

    job://[qual_name]/[rx]

The ``qual_name`` variable is parsed as a regular expression. The ``r``
modifier grants read permissions. The user can read-only access all jobs
attributes for jobs matching the ``qual_name``. The ``x`` modifier grants
execution permissions. The user can enqueue, restart, remove and kill all jobs
matching the ``qual_name``.

These permissions are automatically verified when the user interacts with all
API request handlers in ``core4.api.v1.request.queue``


API handler access
------------------

The structure of the permission scheme **for API handlers** is::

    api://[qual_name]/[crud]*

The ``qual_name`` variable again is parsed as a regular expression matching
the *qualified name* of the API.
the crud scheme following the ``qual_name`` part further divides the permissions
utilizing HTTP methods that can be roughly divided into 4 actions:

* Create
* Retrieve
* Update
* Delete

To see where the individual methods are located, visit the API documentation.

If an API permission does not contain a specific crud scheme, *all Methods are
allowed by default*.
Methods are freely combinable; all the following examples are valid::

    api://[qual_name]
    api://[qual_name]/c
    api://[qual_name]/crd
    api://[qual_name]/crud  <- This is equivalent to the first example


All users who are to be allowed to manage the ``DummyJob`` at *qual_name*
``core4.queue.helper.job.example.DummyJob`` require the following permissions
depending on the exact intended grants::

    api://core4.api.v1.request.queue.job.JobHandler
    api://core4.api.v1.request.queue.job.JobPost
    api://core4.api.v1.request.queue.job.JobStream
    api://core4.api.v1.request.queue.state.QueueHandler
    job://core4.queue.helper.job.example.DummyJob/x

More efficiently, the permission scheme can be expressed as::

    api://core4.api.v1.request.queue.*
    job://core4.queue.helper.job.example.*/x

These permissions are automatically verified when the user interacts with the
API request handlers in ``core4.api.v1.request``


database access
---------------

The structure of the permission scheme **for MongoDB database access** is::

    mongodb://[database]

Please note that the database specification requires an exact match. No
patterns or regular expressions are allowed here. The permission scheme only
supports read-only database access. Additional requirements cannot be defined
with core4. These special access rights have to be managed outside of the
core4 framework. To grant read-only access to the default core4 system database,
a user requires the following permission::

    mongodb://core4


custom access
-------------

The structure of the permission scheme **for custom application keys** is::

    app://[key]

These keys provide a means to define custom permission settings managed by
core4 jobs or the core4 API. For example, we have used these keys to provide
a user/role based regional authorization scheme::

    app://reporting/eu/de/by

Users with the application key ``reporting`` have access to all regions. Users
with the application key ``reporting/eu`` have access to European data. Users
with the application key ``reporting/eu/de`` have access to German data, etc.

Please note that these custom application keys have to be controlled by
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
role is specified with the following core4 configuration keys:

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


**example**::

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
