import importlib
import re
from io import StringIO

import docutils.parsers.rst.directives.body
import docutils.parsers.rst.roles
import sphinx.ext.napoleon
from docutils import core
import core4.util.data
from core4.base.main import CoreBase

EXPECTED_PARTS = ("method", "parameter", "return", "error", "example")


class CoreApiInspector(CoreBase):

    # def container_info(self, container):
    #     if isinstance(container, str):
    #         parts = container.split(".")
    #         modname = ".".join(parts[:-1])
    #         clsname = parts[-1]
    #         try:
    #             mod = importlib.import_module(modname)
    #             cls = getattr(mod, clsname)
    #             obj = cls()
    #         except:
    #             self.logger.error("failed to inspect [%s]", container)
    #             raise StopIteration
    #     else:
    #         obj = container
    #     self.logger.info("inspecting [%s] at [%s]", container, obj.root)
    #     for rule in obj.iter_rule():
    #         self.logger.debug("testing %s", rule)
    #         handler = rule[1]
    #         yield self.handler_info(handler)
    #         # handler_name = self.handler_qual_name(handler)
    #         # yield dict(
    #         #     qual_name=handler_name,
    #         #     version=self.handler_version(handler),
    #         #     author=getattr(handler, "author", None),
    #         #     title=getattr(handler, "title", None),
    #         #     method=self.handler_methods(handler, handler_name)
    #         # )
    #         # for m in method:
    #         #     testname = os.path.join("/tmp", m.upper() + "-" +
    #         #                             handler_name + ".html")
    #         #     self.logger.debug("wrote [%s]", testname)
    #         #     open(testname, "w").write(method[m]["html"])

    # def handler_version(self, handler):
    #     version = getattr(handler, "version", None)
    #     if version:
    #         return version()
    #     return None

    def handler_info(self, handler):
        """
        Provides documentation about the methods of the passed
        :class:`.CoreRequestHandler`.

        :param handler: either ``qual_name`` (str) or a class derived from
                        :class:`.CoreRequestHandler`
        :return:
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
        handler_name = self.handler_qual_name(handler)
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
        method = {}
        for m in ("post", "get", "put", "delete", "head", "patch", "options"):
            meth = handler.__dict__.get(m, None)
            if meth is not None:
                docstring = meth.__doc__
                method[m] = {
                    "doc": None,
                    "html": None,
                    "parser_error": None,
                    "parts": None,
                    "extra_parts": None
                }
                if docstring:
                    html = self._make_html(docstring)
                    method[m].update({
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
        return method

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
