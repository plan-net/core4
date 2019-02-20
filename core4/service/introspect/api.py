#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
core4 request handler (:class:`.CoreRequestHandler`) meta information.
"""

import importlib
import re

import core4.util.data
from core4.base.main import CoreBase

EXPECTED_PARTS = ("method", "parameter", "return", "raise", "example")


class CoreApiInspector(CoreBase):
    """
    :class:`.CoreApiInspector` collects information about core4 API
    :class:`.CoreRequestHandler` method documentation (plain text and HTML).
    """

    def handler_info(self, handler):
        """
        Provides documentation about methods of the passed
        :class:`.CoreRequestHandler`:

        :param handler: either ``qual_name`` (str) or a class derived from
                        :class:`.CoreRequestHandler`
        :return: result of :meth:`.handler_methods`
        """
        if isinstance(handler, str):
            parts = handler.split(".")
            modname = ".".join(parts[:-1])
            clsname = parts[-1]
            try:
                mod = importlib.import_module(modname)
                cls = getattr(mod, clsname)
                handler = cls
            except:
                self.logger.error("failed to inspect [%s]", handler)
                raise
        return self.handler_methods(handler)

    def handler_qual_name(self, handler):
        """
        Delivers the ``qual_name`` of the passed :class:`.CoreRequestHandler`
        or :mod:`tornado` :class:`tornado.web.RequestHandler` class. All core
        requrest handlers return the `meth:`.CoreRequestHandler.qual_name`.
        All :mod:`tornado` request handlers return their  ``__name__``.

        :param handler: request handler class
        :return: ``qual_name`` or ``__name__``
        """
        qn_func = getattr(handler, "qual_name", None)
        if qn_func:
            return qn_func()
        else:
            return handler.__name__

    def handler_methods(self, handler):
        """
        Extract and format request handler ``GET``, ``POST``, ``PUT``,
        ``DELETE``, ``HEAD``, ``PATCH`` and ``OPTIONS`` methods doc string.
        Only implemented methods are extracted. All inherited methods are
        ignored. Further information about the details of the doc string are
        delivered with attributes ``parser_error``, ``parts`` and
        ``extra_parts``:

        * ``doc`` - plain text doc string
        * ``html`` - HTML formatted doc string using :mod:`docutils`
        * ``parser_error`` - list of parsing errors as provided by
          :mod:`docutils`
        * ``parts`` - dict of bool for expected sections using Google doc
          strings (see :mod:`sphinx.ext.napoleon`).
        * ``extra_parts`` - dict of unexpected sections using Google doc
          strings

        The following sections are expected to be documented with Google
        doc strings:

        * **method** - method outline
        * **parameter** - list of parameters
        * **return** - return value
        * **error** - list of exceptions/errors raised by the method
        * **example** - example code using the method

        :param handler: :class:`.CoreRequestHandler` class
        :return: dict with attributes described above
        """
        listing = []
        for method in ("get", "post", "put", "delete", "patch", "options",
                       "head"):
            func = handler.__dict__.get(method, None)
            if func is not None:
                docstring = func.__doc__
                data = {
                    "method": method,
                    "doc": None,
                    "html": None,
                    "parser_error": None,
                    "parts": None,
                    "extra_parts": None
                }
                if docstring:
                    html = self._make_html(docstring)
                    data.update({
                        "doc": docstring,
                        "html": html["body"],
                        "parser_error": html["error"],
                        "parts": html["parts"],
                        "extra_parts": html["extra_parts"]
                    })
                    if html["error"]:
                        self.logger.error(
                            "encountered [%d] errors with [%s]:\n%s",
                            len(html["error"]),
                            self.handler_qual_name(handler),
                            "\n".join(html["error"]))
                listing.append(data)
        return listing

    def _make_html(self, doc):
        expected = dict([(k, False) for k in EXPECTED_PARTS])
        extra = set()
        for line in doc.split("\n"):
            section = re.match("\s*([^\s]+?)s?\s*\:\s*$", line)
            if section:
                title = section.groups()[0].lower()
                if title in expected:
                    expected[title] = True
                else:
                    extra.add(title)
        ret = core4.util.data.rst2html(doc)
        ret['parts'] = expected
        ret['extra_parts'] = list(extra)
        return ret
