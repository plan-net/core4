# import core4.api.v1.application
# import core4.api.v1.httpserver
# import core4.error
# import tornado.web
# import tornado.routing
# import core4.logger.mixin
# import pytest
#
#
# @pytest.fixture(autouse=True)
# def reset():
#     core4.logger.mixin.logon()
#
#
# from contextlib import closing
# import inspect
#
# import tornado.ioloop
# import tornado.testing
# import tornado.simple_httpclient
#
# import pytest
#
# try:
#     iscoroutinefunction = inspect.iscoroutinefunction
# except AttributeError:
#     def iscoroutinefunction(obj):
#         return False
#
#
# def get_test_timeout(pyfuncitem):
#     timeout = pyfuncitem.config.option.async_test_timeout
#     marker = pyfuncitem.get_marker('timeout')
#     if marker:
#         timeout = marker.kwargs.get('seconds', timeout)
#     return timeout
#
#
# def pytest_addoption(parser):
#     parser.addoption('--async-test-timeout', type=float,
#                      help=('timeout in seconds before failing the test '
#                            '(default is no timeout)'))
#     parser.addoption('--app-fixture', default='app',
#                      help=('fixture name returning a tornado application '
#                            '(default is "app")'))
#
#
# # @pytest.mark.tryfirst
# # def pytest_pycollect_makeitem(collector, name, obj):
# #     if collector.funcnamefilter(name) and iscoroutinefunction(obj):
# #         return list(collector._genfunctions(name, obj))
# #
# #
# # @pytest.mark.tryfirst
# # def pytest_pyfunc_call(pyfuncitem):
# #     funcargs = pyfuncitem.funcargs
# #     testargs = {arg: funcargs[arg] for arg in pyfuncitem._fixtureinfo.argnames}
# #
# #     if not iscoroutinefunction(pyfuncitem.obj):
# #         pyfuncitem.obj(**testargs)
# #         return True
# #
# #     try:
# #         event_loop = funcargs['io_loop']
# #     except KeyError:
# #         event_loop = next(io_loop())
# #
# #     if not isinstance(event_loop, tornado.ioloop.IOLoop):
# #         raise TypeError("unsupported event loop:  %s" % type(event_loop))
# #
# #     event_loop.run_sync(
# #         lambda: pyfuncitem.obj(**testargs),
# #         timeout=get_test_timeout(pyfuncitem),
# #     )
# #     return True
#
#
# @pytest.fixture
# def io_loop():
#     """
#     Create a new `tornado.ioloop.IOLoop` for each test case.
#     """
#     loop = tornado.ioloop.IOLoop()
#     loop.make_current()
#     yield loop
#     loop.clear_current()
#     loop.close(all_fds=True)
#
#
# @pytest.fixture
# def http_server(request, io_loop):
#     """Start a tornado HTTP server that listens on all available interfaces.
#
#     You must create an `app` fixture, which returns
#     the `tornado.web.Application` to be tested.
#
#     Raises:
#         FixtureLookupError: tornado application fixture not found
#     """
#     def _http_server
#     http_app = request.getfuncargvalue(request.config.option.app_fixture)
#     server = tornado.httpserver.HTTPServer(http_app)
#     http_server_port = tornado.testing.bind_unused_port()
#
#     server.add_socket(http_server_port[0])
#
#     yield server
#
#     server.stop()
#
#     if hasattr(server, 'close_all_connections'):
#         io_loop.run_sync(server.close_all_connections,
#                          timeout=request.config.option.async_test_timeout)
#
#
# class AsyncHTTPServerClient(tornado.simple_httpclient.SimpleAsyncHTTPClient):
#
#     def initialize(self, *, http_server=None):
#         super().initialize()
#         self._http_server = http_server
#
#     def fetch(self, path, **kwargs):
#         """
#         Fetch `path` from test server, passing `kwargs` to the `fetch`
#         of the underlying `tornado.simple_httpclient.SimpleAsyncHTTPClient`.
#         """
#         return super().fetch(self.get_url(path), **kwargs)
#
#     def get_protocol(self):
#         return 'http'
#
#     def get_http_port(self):
#         for sock in self._http_server._sockets.values():
#             return sock.getsockname()[1]
#
#     def get_url(self, path):
#         return '%s://127.0.0.1:%s%s' % (self.get_protocol(),
#                                         self.get_http_port(), path)
#
#
# @pytest.fixture
# def http_server_client(http_server):
#     """
#     Create an asynchronous HTTP client that can fetch from `http_server`.
#     """
#     with closing(AsyncHTTPServerClient(http_server=http_server)) as client:
#         yield client
#
#
# @pytest.fixture
# def http_client(http_server):
#     """
#     Create an asynchronous HTTP client that can fetch from anywhere.
#     """
#     with closing(tornado.httpclient.AsyncHTTPClient()) as client:
#         yield client
#
#
# """
# a RequestHandler inherts from core4
# * it has a qualname
# * it might have an alias
# * both act as the URL
# * an URL can be extended with path arguments
#
# an Application inherits from core4
# * it has one or more RequestHandlers
#
# """
# class HelloWorldHandler(tornado.web.RequestHandler):
#
#     def get(self):
#         self.write("hello world")
#
#
# class AppWithRoot(core4.api.v1.application.CoreApplication):
#     root = "test1"
#     rules = [
#         (r"/link", HelloWorldHandler),
#         (r"/url", HelloWorldHandler),
#     ]
#
# class AppNoRoot(core4.api.v1.application.CoreApplication):
#     rules = [
#         (r"/link", HelloWorldHandler),
#         (r"/url", HelloWorldHandler),
#     ]
#
# def _test_app():
#     core4.api.v1.application.serve(
#         AppWithRoot,
#         AppNoRoot,
#         debug=True
#     )
#     print("OK")
#
# # @pytest.fixture
# # def app():
# #     return AppWithRoot().application
# #
# # @pytest.fixture
# # def myhttp_server(request):
# #     """Start a tornado HTTP server.
# #
# #     You must create an `app` fixture, which returns
# #     the `tornado.web.Application` to be tested.
# #
# #     Raises:
# #         FixtureLookupError: tornado application fixture not found
# #     """
# #
# #     def _server(app):
# #         io_loop = tornado.ioloop.IOLoop()
# #         io_loop.make_current()
# #
# #         def _close():
# #             io_loop.clear_current()
# #             io_loop.close(all_fds=True)
# #
# #         request.addfinalizer(_close)
# #
# #         server = tornado.httpserver.HTTPServer(app)
# #         server.listen(5001)
# #
# #         def _stop():
# #             server.stop()
# #             if hasattr(server, 'close_all_connections'):
# #                 io_loop.run_sync(server.close_all_connections)
# #         request.addfinalizer(_stop)
# #         return server
# #
# #     return _server
# #
# # @pytest.fixture
# # def myapp1(myhttp_server):
# #     myhttp_server(AppWithRoot().application)
# #
# #
# # # @pytest.mark.gen_test
# # # def test_hello_world(http_client, base_url):
# # #     print(base_url)
# # #     response = yield http_client.fetch(base_url + "/test1/url")
# # #     print(response.body)
# # #     assert response.code == 200
# #
# # @pytest.mark.gen_test
# # def test_hello_world1(myapp1):
# #     from tornado import httpclient
# #     http_client = httpclient.HTTPClient()
# #     try:
# #         response = http_client.fetch("http://localhost:5001/test1/link")
# #         print(response.body)
# #     except httpclient.HTTPError as e:
# #         # HTTPError is raised for non-200 responses; the response
# #         # can be found in e.response.
# #         print("Error: " + str(e))
# #     except Exception as e:
# #         # Other errors are possible, such as IOError.
# #         print("Error: " + str(e))
# #     http_client.close()
# #     import tornado.httpclient
# #
# #
# #     # print(myhttp_server)
# #     rv = requests.get("")
# #     print(rv)
# #     print("OK")
# # #
# # # def test_duplicate_app():
# # #     with pytest.raises(core4.error.Core4SetupError):
# # #         core4.api.v1.application.serve(
# # #             AppWithRoot,
# # #             AppWithRoot,
# # #             debug=True
# # #         )
#
#
#
#
# class MainHandler(tornado.web.RequestHandler):
#     def get(self):
#         self.write("Hello, world!")
#
#
# @pytest.fixture
# def app():
#     return tornado.web.Application([(r"/", MainHandler)])
#
#
# async def test_http_server_client(http_server_client):
#     # http_server_client fetches from the `app` fixture and takes path
#     resp = await http_server_client.fetch('/')
#     assert resp.code == 200
#     assert resp.body == b"Hello, world!"
#
