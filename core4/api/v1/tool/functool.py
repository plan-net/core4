#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Delivers :func:`serve` to serve dedicated :class:`.CoreApiContainer` and
:func:`serve_all` to collect and launch all enabled :class:`.CoreApiContainer`.
"""

from core4.api.v1.tool.serve import CoreApiServerTool


def serve(*args, port=None, address=None, name=None, reuse_port=True,
          routing=None, core4api=True, **kwargs):
    """
    Serve one or multiple :class:`.CoreApiContainer` classes.

    Additional keyword arguments are passed to the
    :class:`tornado.web.Application` object. Good to know keyword arguments
    with their default values from core4 configuration section ``api.setting``
    are:

    * ``debug`` - defaults to ``True``
    * ``compress_response`` - defaults to ``True``
    * ``cookie_secret`` - not so secret default defined

    Additionally the following core4 config settings specify the tornado
    application:

    * ``crt_file`` and ``key_file`` for SSL support, if these settings are
      ``None``, then SSL support is disabled
    * ``allow_origin`` - server pattern to allow CORS (cross-origin resource
      sharing)
    * ``port`` - default port (5001)
    * ``error_html_page`` - default error page with content type ``text/html``
    * ``error_text_page`` - default error page with content tpe ``text/plain``
    * ``card_html_page`` - default card page
    * ``help_html_page`` - default help page

    Each :class:`.CoreApiContainer` is defined by a unique ``root`` URL. This
    ``root`` URL defaults to the project name and is specified in the
    :class:`.CoreApiContainer` class. The container delivers the following
    default endpoints under it's ``root``:

    * ``/_asset`` serving
      :class:`core4.api.v1.request.standard.file.CoreAssetHandler`
    * ``/_info`` serving
      :class:`core4.api.v1.request.standard.info.InfoHandler`

    .. note:: This method creates the required core4 setup including
              the standard core4 folders (see config setting ``folder``,
              the default users and roles (see config setting
              ``admin_username``, ``admin_realname``, ``admin_password``,
              ``user_rolename``, ``user_realname`` and ``user_permission``.

    :param args: class dervived from :class:`.CoreApiContainer`
    :param port: to serve, defaults to core4 config ``api.port``
    :param address: IP address to listen to.  Address may be an empty string or
                    None to listen on all available interfaces.
    :param name: to identify the server, defaults to hostname
    :param reuse_port: tells the kernel to reuse a local socket in
                       ``TIME_WAIT`` state, defaults to ``True``
    :param routing: URL including the protocol and hostname of the server,
                    which will be used to link the APIs and widgets. The
                    difference between ``address`` and ``routing`` are: address
                    is the listening device. Routing represents the URL under
                    which the server is to be contacted and might be used if a
                    proxy routes the requests. To map the proxy behavior this
                    parameter is supposed to reflect the proxy setting.
    :param core4api: add the core4 standard api containers
                     :class:`.CoreApiContainer` and
                     :class:`.CoreWidgetContainer`, defaults to ``True``
    :param kwargs: passed to the :class:`tornado.web.Application` objects
    """
    CoreApiServerTool().serve(*args, port=port, address=address, name=name,
                              reuse_port=reuse_port, routing=routing,
                              core4api=core4api, **kwargs)


def serve_all(project=None, filter=None, port=None, address=None, name=None,
              reuse_port=True, routing=None, **kwargs):
    """
    Serve all core :class:`.CoreApiContainer` classes of a given project and
    one or more filters. All :class:`.CoreApiContainer` with a
    :meth:`.qual_name <core4.base.main.CoreBase.qual_name>` starting with the
    provided filters will be in scope of API application serving.

    For other arguments see :meth:`serve`.

    :param filter: one or multiple str values to filter
                   :meth:`.qual_name <core4.base.main.CoreBase.qual_name>`
                   of the :class:`.CoreApiContainer` to be served.
    :param port: to serve, defaults to core4 config ``api.port``
    :param address: IP address or hostname.  If it's a hostname, the server
                    will listen on all IP addresses associated with the name.
                    Address may be an empty string or None to listen on all
                    available interfaces.
    :param name: to identify the server, defaults to hostname
    :param reuse_port: tells the kernel to reuse a local socket in
                       ``TIME_WAIT`` state, defaults to ``True``
    :param routing: URL including the protocol and hostname of the server,
                    defaults to the protocol depending on SSL settings, the
                    node hostname or address and port
    :param kwargs: passed to the :class:`tornado.web.Application` objects
    """
    CoreApiServerTool().serve_all(project, filter, port, address, name,
                                  reuse_port,
                                  routing, **kwargs)
