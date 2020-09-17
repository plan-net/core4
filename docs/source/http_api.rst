.. _http_api:

############
web services
############


base classes
############

All web service handlers inherit from any of the following base classes:

``core4.api.v1.request.main.CoreRequestHandler``
    core4os request handler parent class
``core4.api.v1.request.tenant.CoreTenantHandler``
    tenant aware request handler parent class
``core4.api.v1.request.websocket.CoreWebSocketHandler``
    web socket parent class

See :doc:`api` and :doc:`core4/api/v1/index` in the API documentation for
further details.


special classes
###############

Three special request handlers do not act as a parent class for request
implementation. These are rather attached to a :class:`CoreApiContainer`
instance to serve static files and to link to other web resources. These classes
are parameterised for their specific use. See for example :ref:`static` about
static file serving.

``core4.api.v1.request.static.CoreStaticFileHandler``
    request handler to deliver static files from relative and absolute
    directories inside your project repository
``core4.api.v1.request.link.CoreLinkHandler``
    request handler to link to other web resources
``core4.api.v1.request.standard.asset.CoreAssetHandler``
    deliver web assets


featured endpoints
##################

The following list of request handlers implement specific functionalities.
These request handlers are delivered through the standard ``CoreApiServer``.

:class:`core4.api.v1.request.job.JobRequest`
    enqueue and control core4 jobs, see also :doc:`job_api`
:class:`core4.api.v1.request.queue.history.JobHistoryHandler`
    retrieves the paginated job state history from ``sys.event``
:class:`core4.api.v1.request.queue.history.QueueHistoryHandler`
    retrieves total and aggregated job counts for past job execution
:class:`core4.api.v1.request.role.main.RoleHandler`
    manages users and roles
:class:`core4.api.v1.request.standard.access.AccessHandler`
    manages database access token
:class:`core4.api.v1.request.standard.event.EventHandler`
    handles event channel interests and delivers events using web sockets
:class:`core4.api.v1.request.standard.event.EventHistoryHandler`
    delivers event history
:class:`core4.api.v1.request.standard.info.InfoHandler`
    retrieves API endpoint details and help
:class:`core4.api.v1.request.standard.login.LoginHandler`
    authenticates users
:class:`core4.api.v1.request.standard.logout.LogoutHandler`
    delivers user logout
:class:`core4.api.v1.request.standard.profile.ProfileHandler`
    delivers details of the current user
:class:`core4.api.v1.request.standard.setting.SettingHandler`
    manages user setting data
:class:`core4.api.v1.request.standard.system.SystemHandler`
    retrieves system state of daemons and operations modes
:class:`core4.api.v1.request.store.StoreHandler`
    general purpose document store based on user permission (app-key)
