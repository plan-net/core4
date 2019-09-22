"""
- OK:  rows and columns
- OK: row header
- OK: sort by column
- columns ordering
- OK: rows filtering in selected columns
- OK: column header
- OK: pagination
- OK: fixed columns
- select columns

row filtering featuring drop-down menus, freetext search, number filters, date filters
user interaction: selection hook
formatting (number, text, alignment, dates)
fixed rows



"""
import json

from core4.base.main import CoreBase
from core4.util.pager import CorePager

CONST_SCRIPT = """
    var table;
    $(document).ready(function() { 
        table = new DataTable(%(options)s);
        table.run();
    });
"""

CONST_CSS = """
    <link rel="stylesheet" href="/_asset/default/table/jexcel/jexcel.css" type="text/css" />
    <link rel="stylesheet" href="/_asset/default/table/jexcel/jsuites.css" type="text/css" />
"""

CONST_JS = """
    <script src="/_asset/default/table/assets/jquery-3.4.0.min.js"></script>
    <script src="/_asset/default/table/jexcel/jexcel.js"></script>
    <script src="/_asset/default/table/jexcel/jsuites.js"></script>
    <script src="/_asset/default/table/jexcel/table.js"></script>
"""

CONST_DIV = """
    <div id="%(_id)s"></div>
"""


class CoreDataTable(CoreBase):

    css = CONST_CSS
    js = CONST_JS

    def __init__(self, url, length, query, _id="data-table", **kwargs):
        super().__init__()
        per_page = kwargs.get("per_page", 20)
        self._option = dict(
            _id=_id,
            url=url,
            method=kwargs.get("method", "GET"),
            current_page=kwargs.get("current_page", 0),
            filter=kwargs.get("filter", None),
            per_page=per_page,
            width=kwargs.get("width", "1000px"),
            height=kwargs.get("height", "400px"),
            column=kwargs.get("column", None)
        )
        self._pager = CorePager(
            current_page=kwargs.get("current_page", 0),
            per_page=per_page,
            length=length,
            query=self.query,
            sort_by=kwargs.get("sort_by", None),
            filter=kwargs.get("filter", None)
        )
        self._query = query

    async def page(self, *args, **kwargs):
        return await self._pager.page(*args, **kwargs)

    async def query(self, *args, **kwargs):
        return await self._query(*args, **kwargs)

    @property
    def div(self):
        return CONST_DIV % dict(_id=self.option("_id"))

    def option(self, key, value=None):
        if value is not None and key in self._option:
            self._option[key] = value
        return self._option[key]

    @property
    def script(self, script_tag=True):
        html = CONST_SCRIPT % dict(
            options=json.dumps(self._option)
        )
        if script_tag:
            html = "<script>" + html + "</script>"
        return html
