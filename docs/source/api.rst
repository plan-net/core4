.. _api:

####################
ReST API and widgets
####################

core4 features an API and mini applications (AKA widgets). The implementation
of an API endpoint starts with a :class:`.CoreRequestHandler`::

    from core4.api.v1.request.main import CoreRequestHandler

    class TestHandler(CoreRequestHandler):

    author = "mra"
    title = "test handler"

    def get(self):
        self.reply("hello world")


This handler supports the ``GET`` method and all other method requests raise a
``405 - Method not allowed`` error.

Next, attach the request handler to a :class:`.CoreApplicationContainer`. Such
a container bundles all request handlers from a functional point of view. From
a technical point of view, all request handlers have the same URL prefix::

    from core4.api.v1.application import CoreApiContainer

    class TestServer(CoreApiContainer):
        root = "/test-server"
        rules = [
            (r'/test', TestHandler)
        ]


The ``root`` property specifies this URL prefix. Therefore the actual
``TestHandler`` endpoint is ``/test-server/test``. The default ``root`` prefix
is the project name.

Use the :meth:`serve` method to start the container::

    from core4.api.v1.application import serve

    serve(TestServer)


You can start multiple :class:`.CoreApplicationContainer` classes with a single
server as in the following example::

    server(TestServer1, TestServer2)


routing rules
#############

core4 is using the same routine rules as :mod:`tornado`. See for example
`Tornado Application Configuration <https://www.tornadoweb.org/en/stable/web.html#application-configuration>`_.

One exception to the standard tornado routing pattern is the
:class:`.CoreStaticFileHandler`. This handler must specify the path name and
core4 will automatically append the directory/file name pattern
``"(?:/(.*))?$"``.


protected handlers
##################

All request handlers inherited from :class:`.CoreRequestHandler` have a
property ``protected = True`` by default. This requires an authenticated and
authorised user login to access the resource handler.

All users with permission ``COP`` (core operators) have access to all resource
handlers. All other users must have a permission pattern matching the
:meth:`.qual_name <core4.base.main.CoreBase.qual_name>` of the resource.

To access the :class:`.QueueHandler` resource located at
``core4.api.v1.request.queue.state.QueueHandler`` the user must for example
have a role with permission
``api://core4.api.v1.request.queue.state.QueueHandler``. Please note that the
permission string is a regular expression. Therefore the permission
``api://core4.api.v1.request.queue`` grants access to all handlers located
below this :meth:`.qual_name <core4.base.main.CoreBase.qual_name>` including
the :class:`.QueueHandler`.

To create a public request handler set the ``protected`` property accordingly::

    from core4.api.v1.request.main import CoreRequestHandler

    class TestHandler(CoreRequestHandler):

    protected = False

    def get(self):
        return "hello world"


.. note:: The login handler at
          :class:`core4.api.v1.request.standard.LoginHandler` and the top level
          :class:`core4.api.v1.request.static.CoreStaticFileHandler` are not
          protected.


response creation
#################

To create a response you can use :mod:`tornado` methods like
:meth:`.write <tornado.web.write>`, :meth:`.flush <tornado.web.flush>` and
:meth:`.finish <tornado.web.finish>` as well as the templating mechanics of
:mod:`tornado` like :meth:`.render <tornado.web.render>`.

core4 introduces an additional method :meth:`.reply` and which supports the
creation of the following media types:

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

The standard json response carries the following attributes:

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


See :ref:`flashing` for an additional response element.


error response format
#####################

If the API throws an exception or returns a HTTP status code of 400 or above,
then the response does not contain the payload ``data`` attribute. Instead an
``error`` attribute carries a short description of the error. If the server
has been started in **DEBUG** mode, then this ``error`` attribute contains the
full stacktrace.

**Example**::

    from core4.api.v1.request.main import CoreRequestHandler
    from tornado.web import HTTPError

    class ErrorTestHandler(CoreRequestHandler):

    def get(self):
        raise HTTPError(409, "this is the ErrorTestHandler")


This handler returns the following response::

    {
        '_id': '5be2d1fcde8b69105ee8b35b',
        'code': 409,
        'message': 'Conflict',
        'timestamp': '2018-11-07T11:52:28.682515',
        'error': 'tornado.web.HTTPError: HTTP 409: Conflict (this is the ErrorTestHandler)\n'
    }


.. _pagination:

pagination
##########

Resource handlers which support pagination must return a :class:`PageResult`
with :meth:`.reply`. This extends the standard json response with  information
about the current page:

* ``page_count`` - the total number of pages
* ``total_count`` - the total number of records
* ``page`` - the current page requested and returned
* ``count`` - the number of records in the current page
* ``per_page`` - the requested number of records per page

**Example**:

The :class:`.CoreApiRequest` :meth:`.JobHandler.get` method returns a paginated
job listing. The method collecting and paginating this job listing is
:meth:`.JobHandler.get_listing`::

    async def get_listing(self):
        """
        Retrieve job listing from ``sys.queue``.

        :return: :class:`.PageResult`
        """

        async def _length(filter):
            return await self.collection("queue").count_documents(filter)

        async def _query(skip, limit, filter, sort_by):
            cur = self.collection("queue").find(
                filter).sort(*sort_by).skip(skip).limit(limit)
            return await cur.to_list(length=limit)

        per_page = int(self.get_argument("per_page", default=10))
        current_page = int(self.get_argument("page", default=0))
        query_filter = self.get_argument("filter", default={})
        sort_by = self.get_argument("sort", default="_id")
        sort_order = self.get_argument("order", default=1)

        pager = CorePager(per_page=int(per_page),
                          current_page=int(current_page),
                          length=_length, query=_query,
                          sort_by=[sort_by, int(sort_order)],
                          filter=query_filter)
        return await pager.page()


The following example session authenticates and retrieves a page from
``sys.queue``::

    from requests import get

    # authenticate
    signin = get("http://localhost:5001/core4/api/v1/login"
                 "?username=admin&password=hans")
    token = signin.json()["data"]["token"]
    header = {"Authorization": "Bearer " + token}

    # get results
    rv = get(
        "http://localhost:5001/coco/v1/jobs?per_page=10&sort=args.id&order=-1",
        headers=header)
    rv.json()
    {
        '_id': '5c0a3ff2de8b697b10f8dd0f',
        'code': 200,
        'message': 'OK',
        'timestamp': '2018-12-07T09:40:02.906633',
        'page': 0,
        'page_count': 1,
        'per_page': 10,
        'total_count': 1.0,
        'count': 1,
        'data': [ ... # removed for brevity
        ]
    }


authentication
##############

The login resource handler :class:`.LoginHandler` accepts the following input
to authenticate a user with his or her password:

#. basic authorization header
#. username and password as query parameters
#. username and password as json body attributes


After successful login, the response body and the HTTP header contain the login
token. The HTTP header also holds a secure cookie which contains the token
(see :class:`LoginHandler <core4.api.v1.request.standard.login.LoginHandler>`).

The client is supposed to send this token or the cookie with each request. The
token can also be sent as a query parameter. For security reason this is
possible though not good practice.

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


If the creation time of the token is older than 1 hour, then a refresh
token is created and sent with the HTTP header (field ``token``).
This refresh time can be configured with setting ``api.token.refresh``.

The purpose of these refresh token is to allow the client to extend the
session. The client must replace the current token (which is still valid) with
the refresh token to continue access.

The lifetime of the initial token is 8 hours. For a smooth user experience
a new refresh token is sent every hour.


.. _api_cods:

API documentation
#################

Each request handler requires the following class properties:

* ``title``
* ``author``

The class doc string is optional and should provide a general introduction to
the purpose of the handler.

Each implemented method ``GET``, ``POST``, ``DELETE``, etc. requires the
following documentation sections. Please note that we use sphinx extension
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
templates::

    class TestHandler(CoreRequestHandler):

        def get(self):
            self.render("template.html")


By default the template path is relative to the resource handler location. You
can modify the template path by setting the ``.template_path`` variable either
as a class property or as a handler argument::


    class TestHandler(CoreRequestHandler):

        template_path = "template"

        def get(self):
            self.render("template.html") # located in <handler>/template


A relative ``.template_path`` as in the example above addresses a directory
relative to the resource handler. An absolute ``.template_path`` addresses a
directory from the project root::

    class TestHandler(CoreRequestHandler):

        template_path = "/api/template"

        def get(self):
            self.render("template.html") # located in <project>/api/template


.. _flashing:

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

core4 extends the general purpose method :meth:`.get_argument` to additionally
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


static file serving
###################

You can specify the folder to serve static files with your request handler::

    class TestHandler(CoreRequestHandler):

        template_path = "/api/template"
        static_path = "/api/template"

        def get(self):
            self.render("template.html") # located in <project>/api/template


This will deliver template files and static files from the same directory
relative to ``TestHandler`` project root at ``/api/template``. You have to
address static files in your template files with the ``static_url`` directive::

    <link rel="stylesheet" type="text/css" href="{{ static_url('style.css') }}">

and for example::

    <img src="{{ static_url('image.png') }}"\>

Both directivrs serve static files ``style.css`` and ``image.png`` from the
specified static directory.

core4 also ships with a default static directory which can used to serve
default styles for example::

    <link rel="stylesheet" type="text/css" href="{{ default_static('default.css') }}">

This default static directory is specified by the core4 config key
``api.default_static``. The default value is ``api/v1/request/_static`` and is
interpreted as a relative path to the core4 package directory. You can
overwrite this setting and also address absolute folders in your file systems.
In the current core4 release the following
default files are defined and are expected to exist in the overwritten default
static folder:

.. todo:: requires the list of default static files


.. warning:: Tornado is not as efficient as a fully fledged web server like
             nginx or apache and should be used only to serve low-traffic
             static sites.

extra endpoints of each handler
###############################

Each handler has three additional endpoints associated with the resource:

#. a help page (``help_url``)
#. a card page (``card_url``)
#. an entry URL (``enter_url``)

The help page delivers well formatted endpoint documentation in HTML following
the guiding principles described at :ref:`api_docs`. The card page provides
relevant endpoint information and can be customised with the
:meth:`.CoreBaseHandler.card` method. The entry URL is the landing page of the
API which defaults to the API ``GET`` method and can be customised with the
handler's class property ``enter_url``.

The following example customises the card page by using a custom template file.
The default card template is located at
``core4/api/v1/request/standard/template``::

    class TestHandler(CoreRequestHandler):

        def card(self):
            self.render("template/card.html") # located in <handler>/api/template


The following example customises the ``enter_url`` and redirects to Serviceplan
when the user enters the API's landing page::

    class TestHandler(CoreRequestHandler):

        enter_url = "http://www.serviceplan.com"

        def get(self):
            return self.reply("OK")


.. _rule_arguments:

handler arguments at rules
##########################

Certain handler properties can be overwritten within the ``rules`` property of
the :class:`.CoreApiContainer` class. These are the following properties:

* ``protected``
* ``title``
* ``author``
* ``tag``
* ``template_path``
* ``static_path``
* ``default_filename``
* ``enter_url``
* ``icon``

This is especially useful when serving static files with
:class:`.CoreStaticFileHandler`::

    class TestContainer(CoreApiContainer):
        root = "/test-server"
        rules = [
            (r'/help', CoreStaticFileHandler, {
                "title": "API introduction",
                "path": "/api/static/help",
                "default_filename": "default.html",
                "protected": False,
                "author": "mra",
                "icon": "help"})
        ]


This is more efficient than subclassing from :class:`.CoreStaticFileHandler` to
define these properties as in the following example::

    class HelpHandler(CoreStaticFileServer):

        author = "mra"
        title = "API introduction"
        path = "/api/static/help"
        default_filename = "default.html"
        protected = False
        icon = "help"

    class TestContainer(CoreApiContainer):
        root = "/test-server"
        rules = [
            (r'/help', HelpHandler)
        ]


handler access in templates
###########################

Template rendering uses the :mod:`tornado` mechanics described at
`Tornado - Flexible Output Generation`_. The :class:`.CoreRequestHandler`
provides additional handler properties available as properties and methods:

* ``request``: request object
* ``qual_name``: of the handler
* ``project``: of the handler
* ``author``: of the handler
* ``tag``: list of the handler
* ``title``: of the handler
* ``template_path``: of the handler
* ``static_path``: of the handler
* ``log_level``: of the handler
* ``token_exp``: expiration date of the current authentication token
* ``started``: start date/time of the request
* ``protected``: indicates if the handler is public or not
* ``config``: core4 configuration dictionary
* ``class_config``: class section of core4 configuration dictionary
* ``icon``: of the handler
* ``identifier``: of the request
* ``user``: user object, see :class:`core4.api.v1.role.model.CoreRole`
* ``enter_url``: landing page URL of the handler
* ``application``: object of the handler, and ``application.container`` with
  the container object of the application and handler
* ``_flash``:


example vue rendering
#####################

core static file with global variable injection
static file with single endpoint to js rendered page


single page applications (SPA)
##############################

tbd.


example vue rendering
#####################

core static file with global variable injection
static file with single endpoint to js rendered page


config overwrite
################

Similar to jobs you can specify a core4 configuration specific for a
:class:`.CoreRequestHandler`. The following attributes overrule the handler's
class properties and arguments defined by the :class:`.CoreApiContainer` (see
:ref:`rule_arguments`):

* log_level
* template_path
* static_path

Assume the following resource ``MyHandler`` is located at
``project/api/v1/handler.py``::

    class MyHandler(CoreRequestHandler):

        author = "mra"
        title = "API introduction"
        template_path = "/project/api/templates"
        icon = "help"

        def get(self):
            return self.render("index.html")


You can overwrite for example the ``template_path`` setting with the following
core4 local configuration::

    project:
      api:
        v1:
          handler:
            MyHandler:
              template_path: /srv/www/custom_templates


multiple process serving
########################

core4 is based on the tornado web framework and asynchronous network library.
Tornado should run on Unix-based platforms. Mac OS X and windows are generally
supported but only recommended for development and testing systems.

Due to the Python GIL (Global Interpreter Lock), it is necessary to run
multiple Python processes to take full advantage of multi-CPU machines. The
tornado maintainers recommend to run one process per CPU.

The most simple setup for core4 is to run multiple instances on a multi-core
server, e.g. to start eight independent ``serve`` or ``serve_all`` commands on
an eight-core server. This means that the following shell command is to be
spawned multiple, i.e. eight times::

    $ coco --application --filter core4.api.v1.server --port 8080 --reuse-port


The ``--reuse-port`` option (defaults to ``True``) tells the kernel to reuse a
local socket in ``TIME_WAIT`` state which essentially means that all proccesses
listen and share the same port, i.e. 8080 in this scenario.


download
########

Download is supported with a :meth:`.CoreRequestHandler.download` method. See
the following example::

    class DownloadHandler(CoreRequestHandler):

        async def get(self):
            await self.download("./static1/asset/test.dat", "test.dat")


For uploading files and especially large files see for example

* `Server does not receive big files`_
* `Mime-type of the stream request body output`_


.. _Tornado - Flexible Output Generation: https://www.tornadoweb.org/en/stable/template.html
.. _Server does not receive big files: https://stackoverflow.com/questions/36688827/tornado-server-does-not-receive-big-files
.. _Mime-type of the stream request body output: https://stackoverflow.com/questions/25529804/tornado-mime-type-of-the-stream-request-body-output
