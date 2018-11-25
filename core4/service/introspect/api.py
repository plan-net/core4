import importlib
import os
import textwrap
from io import StringIO
import re
import docutils.parsers.rst.directives.body
import docutils.parsers.rst.roles
import sphinx.ext.napoleon
from docutils import core
from docutils.parsers.rst.directives import register_directive

from core4.base.main import CoreBase

EXPECTED_PARTS = ("method", "parameter", "return", "error", "example")

class CoreApiInspector(CoreBase):

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.napoleon = sphinx.ext.napoleon.Config(
            napoleon_use_param=False,
            napoleon_use_rtype=True,
            napoleon_google_docstring=True,
            napoleon_numpy_docstring=False,
            napoleon_include_init_with_doc=True,
            napoleon_include_private_with_doc=True,
            napoleon_include_special_with_doc=True,
            napoleon_use_admonition_for_examples=False,
            napoleon_use_admonition_for_notes=True,
            napoleon_use_admonition_for_references=True,
            napoleon_use_ivar=True,
            napoleon_use_keyword=True
        )

    register_directive("method", docutils.parsers.rst.directives.body.Rubric)
    for role in ("exc", "meth", "mod", "class"):
        docutils.parsers.rst.roles.register_local_role(
            role, docutils.parsers.rst.roles.generic_custom_role)

    def make_html(self, doc):
        dedent = textwrap.dedent(doc)
        expected = dict([(k, False) for k in EXPECTED_PARTS])
        extra = set()
        for line in dedent.split("\n"):
            section = re.match("^([^\s]+?)s?\s*\:\s*$", line)
            if section:
                title = section.groups()[0].lower()
                if title in expected:
                    expected[title] = True
                else:
                    extra.add(title)
        google = sphinx.ext.napoleon.GoogleDocstring(
            docstring=dedent, config=self.napoleon)
        err = StringIO()
        parts = core.publish_parts(source=str(google), writer_name="html",
                                   settings_overrides=dict(warning_stream=err))
        err.seek(0)
        errors = [line for line in err.read().split("\n") if line.strip()]
        return {
            'error': errors,
            'body': parts['fragment'],
            'parts': expected,
            'extra_parts': extra
        }

    def info(self, qual_name):
        parts = qual_name.split(".")
        modname = ".".join(parts[:-1])
        clsname = parts[-1]
        try:
            mod = importlib.import_module(modname)
            cls = getattr(mod, clsname)
            obj = cls()
        except:
            self.logger.error("failed to inspect [%s]", qual_name)
            return None
        self.logger.debug("inspecting [%s] at [%s]", qual_name,
                          obj.root)
        for rule in obj.rules:
            self.logger.debug("testing [%s]", rule)
            quality = {}
            handler = rule[1]
            handler_name = self.handler_qual_name(handler)
            author = getattr(handler, "author", None)
            title = getattr(handler, "title", None)
            method = self.handler_methods(handler, handler_name)
            quality["author"] = author is not None
            quality["title"] = title is not None
            # self.logger.debug("%s: author = %s", handler_name, author)
            # self.logger.debug("%s: title = %s", handler_name, title)
            # self.logger.debug("%s: quality = %s", handler_name, quality)
            self.logger.debug("%s: method = %s", handler_name, method)
            for m in method:
                testname = os.path.join("/tmp", m.upper() + "-" +
                                        handler_name + ".html")
                self.logger.debug("wrote [%s]", testname)
                open(testname, "w").write(method[m]["html"])

    def handler_qual_name(self, handler):
        qn_func = getattr(handler, "qual_name", None)
        if qn_func:
            return qn_func()
        else:
            return handler.__name__

    def handler_methods(self, handler, name):
        method = {}
        for m in ("post", "get", "put", "delete", "head", "patch", "options"):
            meth = handler.__dict__.get(m, None)
            if meth is not None:
                docstring = meth.__doc__
                if docstring:
                    html = self.make_html(docstring)
                    method[m] = {
                        "doc": docstring,
                        "html": html["body"],
                        "parser_error": html["error"],
                        "parts": html["parts"],
                        "extra_parts": html["extra_parts"]
                    }
                    if html["error"]:
                        self.logger.error("encountered [%d] errors with [%s]:\n%s",
                                          len(html["error"]), name,
                                          "\n".join(html["error"]))
        return method


if __name__ == '__main__':
    from core4.logger.mixin import logon

    logon()
    inspect = CoreApiInspector()
    inspect.info("core4.api.v1.server.CoreApiServer")
    # inspect.info("project.api.server1.ProjectServer1")
