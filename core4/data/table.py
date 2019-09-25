"""
- OK:  rows and columns
- OK: row header
- OK: rows filtering in selected columns
- OK: column header
- OK: pagination
- OK: fixed columns
- OK: select columns
- OK: formatting (number, text, alignment, dates)
- OK: columns ordering
- OK: sort by column
- OK: user interaction: selection hook

row filtering featuring drop-down menus, freetext search, number filters, date filters
fixed rows
"""
import json

from core4.base.main import CoreBase
from core4.util.pager import CorePager

# javascript instantiation
CONST_SCRIPT = """
    <script>
        var table;
        $(document).ready(function() { 
            table = new DataTable(%(options)s);
            table.update();
        });
    </script>
"""

# jexcel and jquery css/js libraries
CONST_CSS = """
    <link rel="stylesheet" href="/_asset/default/table/jexcel/jexcel.css" type="text/css" />
    <link rel="stylesheet" href="/_asset/default/table/jexcel/jsuites.css" type="text/css" />
"""
CONST_JS = """
    <script src="/_asset/default/table/assets/jquery-3.4.0.min.js"></script>
    <script src="/_asset/default/table/jexcel/jexcel.js"></script>
    <script src="/_asset/default/table/jexcel/jsuites.js"></script>
    <script src="/_asset/default/table/jexcel/datatable.js"></script>
"""

# the datatables containner
CONST_DIV = """
    <div id="%(_id)s"></div>
"""


class CoreDataTable(CoreBase):

    css = CONST_CSS
    js = CONST_JS

    def __init__(self, url, length, query, column, _id="data-table",
                 method="GET",per_page=20, current_page=0, width="1000px",
                 height="400px",sort_by=None, filter=None):
        super().__init__()
        self._option = dict(
            _id=_id,
            url=url,
            method=method,
            current_page=current_page,
            per_page=per_page,
            filter=filter,
            width=width,
            height=height,
            column=column
        )
        self._pager = CorePager(
            length=length,
            query=self.query,
            current_page=current_page,
            per_page=per_page,
            filter=filter,
            sort_by=sort_by
        )
        self._query = query
        self._format = {}
        for column in self._option["column"]:
            self._format[column["name"]] = column["format"]

    async def page(self, *args, **kwargs):
        # deliver page data
        return await self._pager.page(*args, **kwargs)

    async def query(self, *args, **kwargs):
        # query data
        data = []
        for record in await self._query(*args, **kwargs):
            upd = {}
            for field, value in record.items():
                upd[field] = self._format[field].format(value)
            data.append(upd)
        return data

    @property
    def div(self):
        # deliver the DIV tag
        return CONST_DIV % dict(_id=self.option("_id"))

    @property
    def script(self):
        # deliver the javascript instantiation of the
        option = self._option.copy()
        for col in option.get("column", []):
            if "format" in col:
                del col["format"]
        return CONST_SCRIPT % dict(
            options=json.dumps(option)
        )

    def option(self, key, value=None):
        if value is not None and key in self._option:
            self._option[key] = value
        return self._option[key]

