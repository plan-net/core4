#################
events processing
#################

Event processing is supported with core4 endpoint ``/core4/api/v1/event``.
See also :doc:`message`.

The following events are defined:

* ``enqueue_job`` - a job is enqueued
* ``request_start_job`` - a job has been requested to start by
  :class:`.CoreWorker`
* ``start_job`` - a job is started by :class:`.CoreWorkerProcess`
* ``complete_job`` - a job has successfully finished processing
* ``defer_job`` - a job has deferred processing
* ``failed_start`` - a job failed to start
* ``failed_job`` - a job has failed processing
* ``request_remove_job`` - a job has been requested to be removed
* ``remove_job`` - a job has been removed
* ``request_kill_job`` - a job has been requested to be killed
* ``kill_job`` - a job has been killed
* ``flag_nonstop`` - a job has been flagged as a non-stopping job
* ``flag_zombie`` - a job has been flagged as a zombie job
* ``inactivate_job`` - a job has been set inactive
* ``restart_waiting`` - a job in waiting state (pending, failed, deferred) has
  been restarted
* ``restart_stopped`` - a job in stopped state (killed, error, inactive) has
  been restarted


The following example creates a user with proper access permissions to query
the job queue history. After retrieval of the queue history the example
connects to the event web socket.

.. note:: The example requires installation of package :mod:`websocket`.
          Install the package with ``pip install websocket``.

Login with an administrative user (role _cop_) to create a new user.

.. code-block:: python

    from requests import post, get, put

    login = get("http://devops:5001/core4/api/login?username=admin&password=hans")
    token = login.json()["data"]["token"]

    rv = post("http://devops:5001/core4/api/v1/roles",
              headers={"Authorization": "Bearer " + token},
              json={
                  "name": "test",
                  "realname": "Test User",
                  "email": "test@plan-net.com",
                  "password": "very secret",
                  "role": ["standard_user"],
                  "perm": ["api://core4.api.v1.request.queue.history.*"]
              })
    assert rv.status_code == 200
    etag = rv.json()["data"]["etag"]


The created user *test* has access to all standard endpoints through role
*standard user*. This includes :class:`.EventHandler` located at
``/core4/api/v1/event``. The additional access permissions granted to user
_test_ include :class:`.JobHistory` located at ``/core4/api/v1/jobs/history``.

Use the latter to retrieve the paginated state history of ``sys.queue``. Use
the event handler to retrieve real-time updates afterwards. The following
session exemplifies this workflow.

.. code-block:: python

    user_login = get("http://devops:5001/core4/api/login?username=test&password=very secret")
    user_token = user_login.json()["data"]["token"]

    rv = get("http://devops:5001/core4/api/v1/jobs/history?token=" + user_token)


Paginate through the results following the core4 pager approach.

.. code-block:: python

    url = "http://devops:5001/core4/api/v1/jobs/history?token=" + user_token

    rv = get(url + "&page=1")
    rv = get(url + "&page=2")

The output reflects the historical queue states in reverse sort order::

    {'_id': '5c8fd974ad70711051793fa2',
     'code': 200,
     'count': 10,
     'data': [{'created': '2019-03-18T17:44:54', 'total': 0},
              {'created': '2019-03-18T17:44:51', 'running': 1, 'total': 1},
              {'created': '2019-03-18T17:44:50', 'running': 1, 'total': 1},
              {'created': '2019-03-18T17:44:49', 'pending': 1, 'total': 1},
              {'created': '2019-03-18T17:44:45', 'total': 0},
              {'created': '2019-03-18T17:44:42', 'running': 1, 'total': 1},
              {'created': '2019-03-18T17:44:41', 'running': 1, 'total': 1},
              {'created': '2019-03-18T17:44:40', 'pending': 1, 'total': 1},
              {'created': '2019-03-18T17:44:22', 'total': 0},
              {'created': '2019-03-18T17:44:19', 'running': 1, 'total': 1}],
     'message': 'OK',
     'page': 0,
     'page_count': 2,
     'per_page': 10,
     'timestamp': '2019-03-18T17:46:28.263495',
     'total_count': 16.0}


For real-time updates connect to the web socket at ``/core4/api/v1/event`` and
announce interest in channel ``queue``.

.. code-block:: python

    from websocket import create_connection
    import json

    ws = create_connection("ws://devops:5001/core4/api/v1/event?token=" + user_token)
    ws.send(json.dumps({"type": "interest", "data": ["queue"]}))
    print(ws.recv())
    while True:
        print(ws.recv())


In order to encounter updates you should enqueue jobs and start a worker. Open
up another terminal, enqueue some jobs and start a worker.

.. code-block:: shell

    coco --enqueue core4.queue.helper.job.example.DummyJob sleep=10
    coco --worker


With this single job and a running worker you will see the following _queue_
events with your web socket connection:

* ``enqueue_job``
* ``request_start_job``
* ``start_job``
* ``complete_job``

Additionally there are multiple ``summary`` events listing the aggregated
``sys.queue`` states. Since the querying user does not have access permissions
on the started job ``core4.queue.helper.job.example.DummyJob`` the job summary
sanitises the aggregated job states as ``UnauthorizedJob`` instead.

See the following _queue_ stream. This stream has been processed after a single
job ``core4.queue.helper.job.example.DummyJob`` has been enqueued and
processed::

     # interest confirmation message
     {'data': ['queue'],
      'message': "processed interest in ['queue']",
      'type': 'interest'},

     # event "enqueued_job"
     {'_id': '5c8fd9d7ad707128553646d7',
      'author': 'mra',
      'channel': 'queue',
      'created': '2019-03-18T17:48:07',
      'data': {'_id': '5c8fd9d7ad707128553646d6', 'queue': {'pending': 1}},
      'name': 'enqueue_job'},

     # sys.queue.summary event after the job has been enqueued
     {'author': 'mra',
      'channel': 'queue',
      'created': '2019-03-18T17:48:07',
      'data': [{'killed': False,
                'n': 1,
                'name': 'UnauthorizedJob',
                'removed': False,
                'state': 'pending',
                'wall': False,
                'zombie': False}],
      'name': 'summary'},

     # event "request_start_job" after the worker has consumed the job
     {'_id': '5c8fd9d8ad70711067b48666',
      'author': 'mra',
      'channel': 'queue',
      'created': '2019-03-18T17:48:08',
      'data': {'_id': '5c8fd9d7ad707128553646d6', 'queue': {'running': 1}},
      'name': 'request_start_job'},

     # sys.queue.summary event after the job has been sent the processor
     {'author': 'mra',
      'channel': 'queue',
      'created': '2019-03-18T17:48:08',
      'data': [{'killed': False,
                'n': 1,
                'name': 'UnauthorizedJob',
                'removed': False,
                'state': 'running',
                'wall': False,
                'zombie': False}],
      'name': 'summary'},

     # event "start_job" after the processor confirmed to process the job
     {'_id': '5c8fd9d9ad707128be5070b9',
      'author': 'mra',
      'channel': 'queue',
      'created': '2019-03-18T17:48:09',
      'data': {'_id': '5c8fd9d7ad707128553646d6', 'queue': {'running': 1}},
      'name': 'start_job'},

     # event "complete_job" after the processor has completed job processing
     {'_id': '5c8fd9e3ad707128be5070c8',
      'author': 'mra',
      'channel': 'queue',
      'created': '2019-03-18T17:48:19',
      'data': {'_id': '5c8fd9d7ad707128553646d6', 'queue': {}},
      'name': 'complete_job'},

     # sys.queue.summary event after the job has been completed
     {'author': 'mra',
      'channel': 'queue',
      'created': '2019-03-18T17:48:19',
      'data': [],
      'name': 'summary'}]


.. note:: The event ``summary`` is time based. The job summary is created every
          second. In contrast to this all other events in channel ``queue`` are
          based on jobs' state changes. For this reason the ``summary`` events
          will not reflect all state changes in ``sys.queue`` and the same
          process flow will not produce the same event flow if executed
          multiple times.
