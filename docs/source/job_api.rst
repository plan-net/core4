.. _job_api:

Job Management API
==================

core4 ships with an API to enqueue and control jobs. In detail this API supports

* listing of available jobs
* enqueuing of jobs
* streaming job states, progress and logging
* retrieve running jobs
* retrieve details of current and past jobs
* kill, restart and remove jobs

The following code snippets demonstrate the usage of the job management API.

List Jobs
---------

The list of available jobs is retrieved as a paginated list:

   >>> from requests import get
   >>> rv = get("http://localhost:5001/core4/api/v1/job/list",
   ...          auth=("admin", "hans"))
   >>> rv.json()

You can control pagination and filtering with the parameters ``page``,
``per_page``, ``sort`` and ``filter``. The following snippet filters for the
*dummy job*:

   >>> rv = get("http://localhost:5001/core4/api/v1/job/list?page=0&search=dummy",
   ...          auth=("admin", "hans"))
   >>> rv.json()

Enqueue Jobs
------------

Use the ``qual_name`` to enqueue the job and the ``args`` parameter to deliver
payload into the job:

   >>> from requests import post
   >>> rv = post("http://localhost:5001/core4/api/v1/job",
   ...           json={
   ...               "qual_name": "core4.queue.helper.job.example.DummyJob",
   ...               "args": {"sleep": 60}
   ...           },
   ...           auth=("admin", "hans"), stream=True)
   >>> for line in rv:
   ...     print(line)

The default behavior of *enqueue* is to send the job *state* and logging (*log')
events as SSE. The end of job is indicated with a *close* event. Please note
that the ``post`` method needs a ``stream=True`` parameter to process the SEE
content properly.

Job Details
-----------

After completion you can access the details of the job using the ``_id``. See
the streamed lines above for the job ``_id``. This id is available in the
``identifier`` attribute of the logging stream and the ``data._id`` element of
the state stream.

   >>> rv = get("http://localhost:5001/core4/api/v1/job/5f6252b42e84fa29038a3e3f",
   ...          auth=("admin", "hans"))
   >>> rv.json()

Note that job details are available for current and past jobs.

Queue Listing
-------------

Launch another job. This time we will not follow job progress. Instead we will
investigate the queue, then kill the job, then restart the job and finally
follow the restarted job.

   >>> rv = post("http://localhost:5001/core4/api/v1/job",
   ...           json={
   ...               "qual_name": "core4.queue.helper.job.example.DummyJob",
   ...               "args": {"sleep": 60},
   ...               "follow": False
   ...           },
   ...           auth=("admin", "hans"), stream=True)
   >>> jid = rv.json()["data"]

Next retrieve the current queue. The result is paginated.

   >>> rv = post("http://localhost:5001/core4/api/v1/job/queue",
   ...           json={"search": "dummy"},
   ...           auth=("admin", "hans"))
   >>> rv.json()

Please note that ``GET /job`` and ``POST /job/queue`` deliver the same results.

Job Control
-----------

Let's kill this job:

   >>> from requests import put
   >>> rv = put("http://localhost:5001/core4/api/v1/job/kill/" + jid,
   ...           auth=("admin", "hans"))
   >>> rv.json()

And restart this job. Please note that the default behavior of *restart* is to
stream the job state changes and logging by default. We disable this behavior
with the ``follow`` argument.

   >>> rv = put("http://localhost:5001/core4/api/v1/job/restart/" + jid,
   ...           json={"follow": False},
   ...           auth=("admin", "hans"))
   >>> rv.json()
   >>> new_jid = rv.json()["data"]

Also note that the restarted job has a new job ``_id``. The journaled job is
available with the *details* endpoint, too.

   >>> rv = get("http://localhost:5001/core4/api/v1/job/" + new_jid,
   ...           auth=("admin", "hans"))
   >>> rv.json()
   >>> print(rv.json()["data"]["state"])

   >>> rv = get("http://localhost:5001/core4/api/v1/job/" + jid,
   ...           auth=("admin", "hans"))
   >>> rv.json()
   >>> print(rv.json()["data"]["state"])

Let's follow the job state changes and logging

   >>> rv = get("http://localhost:5001/core4/api/v1/job/follow/" + new_jid,
   ...          json={"follow": True},
   ...          auth=("admin", "hans"),
   ...          stream=True)
   >>> for line in rv:
   ...     print(line)

There is another request which delivers only the logging of the job. This
response can be streamed (``follow is True``) or paginated
(``follow is False``).

   >>> rv = get("http://localhost:5001/core4/api/v1/job/log/" + new_jid,
   ...          json={"follow": True},
   ...          auth=("admin", "hans"),
   ...          stream=True)
   >>> for line in rv:
   ...     print(line)

But let's kill and remove the job for now:

   >>> rv = put("http://localhost:5001/core4/api/v1/job/kill/" + new_jid,
   ...           auth=("admin", "hans"))
   >>> rv.json()

   >>> rv = put("http://localhost:5001/core4/api/v1/job/remove/" + new_jid,
   ...           auth=("admin", "hans"))
   >>> rv.json()

The job queue is empty for now:

   >>> rv = get("http://localhost:5001/core4/api/v1/job",
   ...           auth=("admin", "hans"))
   >>> rv.json()
