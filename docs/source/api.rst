.. _api:

####################
ReST API and widgets
####################

core4 features an API and mini applications (AKA widgets). The implementation
of an API endpoint starts with a :class:`.CoreRequestHandler`::

    from core4.api.v1.request.main import CoreRequestHandler

    class TestHandler(CoreRequestHandler):

    def get(self):
        self.reply("hello world")


This handler supports only the ``GET`` method and all other method requests
raise a ``405 - Method not allowed`` error.

All request handlers have to be attached to a
:class:`.CoreApplicationContainer`::

    from core4.api.v1.application import CoreApiContainer

    class TestServer(CoreApiContainer):
        root = "/test-server"
        rules = [
            (r'/test', TestHandler)
        ]


The ``root`` property specifies the URL prefix. Therefore the actual
``TestHandler`` endpoint is ``/test-server/test``. The default ``root`` prefix
is the project name.

Use the :meth:`serve` method to start the container::

    from core4.api.v1.application import serve

    serve(TestServer)


You can attach multiple :class:`.CoreApplicationContainer` classes to a server
as in the following example::

    server(TestServer1, TestServer2)


The diagram below depicts the relationship between
:class:`.CoreRequestHandler`, :class:`.CoreApplicationContainer` and
:class:`.CoreApplication`.

.. figure:: _static/api.png
   :scale: 100 %
   :alt: API class relations


routing rules
#############

core4 is using the same routine rules as :mod:`tornado`. See for example
`Tornado Application Configuration <https://www.tornadoweb.org/en/stable/web.html#application-configuration>`_


protected handlers
##################

All request handlers inherited from :class:`.CoreRequestHandler` have a
property ``protected = True`` by default. This requires an authenticated and
authorised user login to access the resource handler.

All users with permission ``COP`` (core operators) have access to all resource
handlers. All other users must have a permission pattern matching the
:meth:`.qual_name <core4.base.main.CoreBase.qual_name>` of the resource.

To access the :class:`.QueueHandler` resource located at
``core4.api.v1.request.queue.state.QueueHandler`` the user must have a role
with permission ``api://core4.api.v1.request.queue.state.QueueHandler``. Please
note that the permission string represents a pattern. Therefore the permission
``api://core4.api.v1.request.queue`` grants access to all handlers located
below this :meth:`.qual_name <core4.base.main.CoreBase.qual_name>` including
the :class:`.QueueHandler`.

To create a public request handler set the ``protected`` property accordingly::

    from core4.api.v1.request.main import CoreRequestHandler

    class TestHandler(CoreRequestHandler):

    protected = False

    def get(self):
        return "hello world"


response creation
#################

To create a response you can use :mod:`tornado` methods like
:meth:`.write <tornado.web.write>`, :meth:`.flush <tornado.web.flush>` and
:meth:`.finish <tornado.web.finish>` as well as the templating mechanics of
:mod:`tornado` like :meth:`.render <tornado.web.render>`.

core4 introduces one additional method :meth:`.reply` to create the following
media types:

* application/json
* text/html
* text/csv
* text/plain

Depending on the variable type passed to :meth:`.reply` and the ``Accept``
header of the client requesting the resource, the response media type is
modified. A :mod:`pandas` DataFrame passed to :meth:`.reply` is transformed
into a json dict (application/json), a HTML table (text/html), a CSV format
(text/csv) or a plain text table (text/plain).

A :class:`.PageResult` variable passed to :meth:`.reply` returns additional
attributes. See :ref:`pagination`.


.. _default-response:

response format
###############

The standard json resopnse carries the following attributes:

* ``_id`` - the request _id
* ``code`` - the HTTP response code
* ``message`` - the HTTP response reason
* ``timestamp`` - the timestamp of the request/response
* ``data`` - the payload

The reponse of the example request handler above is::

    {
        '_id': '5be13b56de8b69468b7ff0b2',
        'code': 200,
        'message': 'OK',
        'timestamp': '2018-11-06T06:57:26.660093',
        'data': "hello world"
    }


error response format
#####################

If the API throws an exception or returns a HTTP status code greater than 200,
then the response does not contain the payload ``data`` attribute. Instead an
``error`` attribute carries a short description of the error. If the server
has been started in **DEBUG** mode, then this ``error`` attribute contains the
full stacktrace.

All resource handlers derived from :class:`.CoreRequestHandler` feature a
method :meth:`.abort` to send a HTTP error response to the client.

**Example**::

    from core4.api.v1.request.main import CoreRequestHandler

    class ErrorTestHandler(CoreRequestHandler):

    def get(self):
        self.abort(400, "this is the ErrorTestHandler")


This handler returns the following response::

    {
        '_id': '5be2d1fcde8b69105ee8b35b',
        'code': 400,
        'message': 'Bad Request',
        'timestamp': '2018-11-07T11:52:28.682515'
        'error': 'this is the ErrorTestHandler',
    }


.. _pagination:

pagination
##########

Resource handlers which support pagination must return a :class:`PageResult`
with :meth:`.reply`. This extends the standard json response with several
information about current page:

* ``page_count`` - the total number of pages
* ``total_count`` - the total number of records
* ``page`` - the current page requested and returned
* ``count`` - the number of records in the current page
* ``per_page`` - the requested number of records per page

**Example**::

            >>> rv = get(url + "/jobs?per_page=10&sort=args.id&order=-1",
                         headers=h)
            >>> rv.json()
            {
                '_id': '5be13b56de8b69468b7ff0b2',
                'code': 200,
                'message': 'OK',
                'timestamp': '2018-11-06T06:57:26.660093',
                'total_count': 50.0,
                'count': 10,
                'page': 0,
                'page_count': 5,
                'per_page': 10,
                'data': [ ... ]
            }


authentication
##############

The login resource handler :class:`.LoginHandler` accepts the following input
to authenticate a user with his or her password:

#. basic authorization header
#. Username and password as query parameters
#. username and password as json body attributes


After successful login, the response body and the HTTP header contain the login
token. The HTTP header also holds a secure cookie which contains the token
(see :class:`LoginHandler <core4.api.v1.request.standard.login.LoginHandler>`).

The client is supposed to send this token or the cookie with each request. The
token can also be sent as a query parameter. For security reason this is not
good practice, but possible.

The following example demonstrates the login procedure, responses and access
to a protected resource using the token::

    from requests import get, post

    url = "http://localhost:5001/core4/api/v1"
    rv = get(url + "/login?username=admin&password=hans")
    rv.json()
    {
        '_id': '5bd94d9bde8b6939aa31ad88',
        'code': 200,
        'data': {
            'token': 'eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9...'
        },
        'message': 'OK',
        'timestamp': '2018-10-31T06:37:15.734609'
    }

    rv.headers
    {
        'Access-Control-Allow-Headers': 'access-control-allow-origin,authorization,content-type',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Origin': '*',
        'Content-Length': '339',
        'Content-Type': 'application/json; charset=UTF-8',
        'Date': 'Wed, 31 Oct 2018 06:37:15 GMT',
        'Etag': '"d62ecba1141f2653ebd4d9a54f677701e3f6337f"',
        'Server': 'TornadoServer/5.1.1',
        'Set-Cookie': 'token="2|1:0|10:1540967835|5:token|280:ZXlK..."; '
        'expires=Fri, 30 Nov 2018 06:37:15 GMT; Path=/',
        'Token': 'eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjo...'
    }

    signin = post(url + "/login",
                  json={"username": "admin", "password": "hans"})
    token = signin.json()["data"]["token"]
    headers = {"Authorization": "Bearer " + token}
    get("http://localhost:5001/core4/api/v1/profile", headers=headers)
    <Response [200]>
    get("http://localhost:5001/core4/api/v1/profile", cookies=signin.cookies)
    <Response [200]>


If the creation time of the token is older than 1h, then a refresh
token is created and sent with the HTTP header (field ``token``).
This refresh time can be configured with setting ``api.token.refresh``.

The purpose of these refresh token is to allow the client to extend the
session. The client must replace the current token (which is still valid) with
the refresh token to continue access.

The lifetime of the initial token is 8h.


API documentation
#################

Each request handler requires the following class properties:

* ``title``
* ``author``

The class doc string is optional and should provide a general introduction to
the purpose of the handler.

Each method ``GET``, ``POST``, ``DELETE``, and ``PUT`` requires the following
documentation sections. Please note that we use sphinx extension
:mod:`sphinxcontrib-napoleon` for endpoint documentation.

* **Methods** - for seperate routing handlers, e.g. with or without URL
  parameters
* **Parameters** - listing of the accepted parameters
* **Returns** - short description and listing of return attributes
* **Raises** - listing of HTTP error codes potentially raised
* **Examples** - how to use the handler

See for example the source code of method
:meth:`GET<core4.api.v1.request.queue.JobHandler.get>` of :class:`.JobHandler`
on how to document multiple routing requests.


templating
##########

Use :mod:`tornado` templating system with method :meth:`.render` to render
templates relative to the resource handler location::

    class TestHandler(CoreRequestHandler):

        def get(self):
            self.render("template.html")


static files
############

You can specify a folder and URL to serve static files with
your :class:`CoreApiContainer`:

* **path** defines the relative or absolute path of the static file folder
* **default_filename** defines the file name to serve from folders (defaults to
  ``index.html``)
* **static_url** defines the URL after ``root`` prefix to serve static files

**Example**::

    class CoreApiServer(CoreApiContainer):
        root = "test"
        path = "html"
        default_filename = "index.htm"
        static_url = 'files'

        rules = [
        ]

This container serves only static files from directory ``./html``


message flashing
################

Use methods :meth:`.flash_debug`, :meth:`.flash_info`, :meth:`.flash_warning`
and :meth:`.flash_error` to send additional messages with the response to the
client.

**Example**::

    class TestHandler(CoreRequestHandler):

        def get(self):
            self.flash_debug("first flash message")
            self.flash_debug("another flash message")
            self.reply("OK")


The response format of this request handler::

    {
        "_id": "5be19c8fde8b695e7cc2ddeb",
        "message": "OK",
        "code": 200,
        "timestamp": "2018-11-06T13:52:15.593395",
        "data": "OK",
        "flash": [
            {
                "level": "DEBUG",
                "message": "first flash message"
            },
            {
                "level": "INFO",
                "message": "another flash message"
            }
        ],
    }


argument parsing
################

:mod:`tornado` supports argument parsing. See `request handler input
<https://www.tornadoweb.org/en/stable/web.html?highlight=get_argument#input>`_.

core4 extends the general purpose methods :meth:`.get_argument` to additionally
facilitate the extraction of arguments from a json content body.

:meth:`.CoreRequestHandler.get_argument` also processes an optional argument
``as_type`` to convert argument types. The method parses the types ``int``,
``float``,  ``bool`` (using :meth:`parse_boolean
<core4.util.data.parse_boolean>`), ``str``, ``dict`` and ``list`` (using
:mod:`json.loads`) and ``datetime`` (:meth:`dateutil.parser.parse`).

The following request handler demonstrates the standardised parsing of
date/time arguments. The ``GET`` method expects the arguments as query
parameters. The ``POST`` method expects the arguments as valid json
attributes. Both methods are based on the same implementation logic and
:meth:`.get_argument` combines parsing from the query string, from the
json body and also from the URL-encoded form (not in scope of this example)::

    import datetime
    from core4.api.v1.application import CoreApiContainer, serve
    from core4.api.v1.request.main import CoreRequestHandler


    class ArgTestHandler(CoreRequestHandler):

        def get(self):
            dt = self.get_argument("dt", as_type=datetime.datetime, default=None)
            if dt:
                delta = (datetime.datetime.utcnow() - dt).total_seconds()
            else:
                delta = 0
            self.reply(
                "got: %s (%dsec. to now)" % (dt, delta))


    class CoreApiServer(CoreApiContainer):
        root = "args"
        rules = [
            (r'/test', ArgTestHandler)
        ]


    if __name__ == '__main__':
        serve(CoreApiServer)


The following commands login and test the date/time parsing using query
parameters with the ``GET`` method::

    >>> from requests import get, post
    >>>
    >>> signin = get("http://localhost:5001/args/login?username=admin&password=hans")
    >>>
    >>> # query parameter, date only
    >>> rv = get("http://localhost:5001/args/test?dt=2018-11-07", cookies=signin.cookies)
    >>> rv.json()
    {
        '_id': '5be30a20de8b69343bd90680',
        'code': 200,
        'data': 'got: 2018-11-07 00:00:00 (57120sec. to now)',
        'message': 'OK',
        'timestamp': '2018-11-07T15:52:00.304976'
    }
    >>>
    >>> # query parameter, date and time
    >>> rv = get("http://localhost:5001/args/test?dt=1971-06-14T07:30:00", cookies=signin.cookies)
    >>> rv.json()
    {
        '_id': '5be30a42de8b69343bd90685',
        'code': 200,
        'data': 'got: 1971-06-14 07:30:00 (1495873354sec. to now)',
        'message': 'OK',
        'timestamp': '2018-11-07T15:52:34.883295'
    }
    >>>
    >>> # query parameter, date, time and timezone
    >>> rv = get("http://localhost:5001/args/test?dt=1971-06-14T07:30:00 CET", cookies=signin.cookies)
    >>> rv.json()
    {
        '_id': '5be30a56de8b69343bd9068a',
        'code': 200,
        'data': 'got: 1971-06-14 06:30:00 (1495876974sec. to now)',
        'message': 'OK',
        'timestamp': '2018-11-07T15:52:54.510046'
    }

The following commands test the same date/time parsing using json bodies
with the ``POST`` method::

    >>> payload = {"dt": "1971-06-14T07:30:00 CET"}
    >>> rv = post("http://localhost:5001/args/test", json=payload, cookies=signin.cookies)
    >>> rv.json()
    {
        '_id': '5be30ae5de8b69343ba1448a',
        'code': 200,
        'data': 'got: 1971-06-14 06:30:00 (1495877117sec. to now)',
        'message': 'OK',
        'timestamp': '2018-11-07T15:55:17.417723'
    }
