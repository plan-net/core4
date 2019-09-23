"""
- OK:  rows and columns
- OK: row header
- OK: rows filtering in selected columns
- OK: column header
- OK: pagination
- OK: fixed columns
- OK: select columns
- OK: formatting (number, text, alignment, dates)
- columns ordering
- sort by column

row filtering featuring drop-down menus, freetext search, number filters, date filters
user interaction: selection hook
fixed rows



"""
import json

from core4.base.main import CoreBase
from core4.util.pager import CorePager

CONST_SCRIPT = """
    <script>
        var table;
        $(document).ready(function() { 
            table = new DataTable(%(options)s);
            table.update();
        });
    </script>
"""

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
        return await self._pager.page(*args, **kwargs)

    async def query(self, *args, **kwargs):
        data = []
        print(self._format)
        for record in await self._query(*args, **kwargs):
            upd = {}
            for field, value in record.items():
                upd[field] = self._format[field] % value
            data.append(upd)
        return data

    @property
    def div(self):
        return CONST_DIV % dict(_id=self.option("_id"))

    @property
    def script(self):
        return CONST_SCRIPT % dict(
            options=json.dumps(self._option)
        )

    def option(self, key, value=None):
        if value is not None and key in self._option:
            self._option[key] = value
        return self._option[key]

