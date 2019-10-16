#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Data Table support providing :class:`.CoreDataTable`.

The following example demonstrates the class in action::

    COLS = [
        {
            "name": "_id",
            "label": None,
            "key": True,
            "hide": True,
            "sortable": False,
            "click": None,
            "align": None,
            "format": "{}",
            "editable": False
        }
    ]

    class TableHandler(CoreRequestHandler):
        author = "mra"
        title = "CoreDataTable example"

        async def _length(self, filter):
            return await self.collection.count_documents(filter)

        async def _query(self, skip, limit, filter, sort_by):
            return await self.collection.find(filter).sort(
                sort_by).skip(skip).limit(limit).to_list(limit)

        def initialize_request(self, *args, **kwargs):
            self.collection = self.config.tests.data1_collection
            args = dict(
                length=self._length,
                query=self._query,
                column=COLS,
                fixed_header=self.get_argument("fixed_header", bool, default=True),
                hide_header=self.get_argument("hide_header", bool, default=False),
                multi_sort=True,
                height=None,
                dense=self.get_argument("dense", bool, default=True),
                select=False,
                multi_select=False,
                search=True,
                per_page=self.get_argument("per_page", int, default=10),
                page=self.get_argument("page", int, default=0),
                filter=self.get_argument("filter", dict, default=None,
                                         dict_decode=convert),
                sort_by=self.get_argument("sort", list, default=None)
            )
            self.datatable = CoreDataTable(**args)

        async def post(self):
            self.reply(
                await self.datatable.post()
            )

        async def get(self):
            self.reply(
                await self.datatable.get()
            )

Given that the collection ``data1_collection`` contains multiple documents,
this handler initialises the data table and passes the ``POST`` and ``GET``
request to the appropriate data table methods.

The Python class manages pagination, filtering and sorting and specifies the
following attributes of the HTML component:

fixed-header
    fixed header to top of table
hide-header
    hide the row header
multi-sort
    If ``True`` then one can sort on multiple properties. The actual sort
    behavior is controlled with the ``sort`` property, see below
height
    set an explicit height of table
dense
    decreases the height of rows
select
    shows the select checkboxes in both the header and row.
multi-select
    changes selection mode to multi select
search
    displays the search bar
per_page
    changes how many items per page should be visible
page
    changes which page of items is displayed
filter
    query json using MongoDB extended query syntax
data
    list of dictionary representing column names (keys) and values

The ``column`` property is a list of dict with the following column
specification:

hide
    indicates that the column is hidden
sortable
    indicates that the table can be sorted by the column
key
    indicates that the column represents the row index. There can be only one
    column where ``.key is True``
name
    technical column name
label
    column name
align
    aligns the column data (left, right, center)
clickable
    backend endpoint if the user clicks the cell (column and row)
format
    column cell format definition  using Python format strings
editable
    indicates that the user can move the column (column sort order)

The ``sort`` property specifies the sort order which is implemented by the
backend.

name
    technical column name
ascending
    indicates sort order
"""

from core4.util.pager import CorePager
import datetime
import bson
from core4.base.main import CoreBase


def convert(obj):
    # special json hook to parse typed mongodb query
    # the hook parses 1) datetime objects and 2) objectid objects
    #
    # example of a date range filter converting a string into a valid
    #   datetime object:
    #
    # { "timestamp": { "$gte": { "$datetime": "2014-04-01T00:00:00" } } }
    #
    # example of a object id filter converting a string into a valid
    #   bson object id:
    #
    # { "_id": { "$objectid": "5d8af9cbad70712cbe0521f7" } }
    for key, value in obj.items():
        if isinstance(key, str):
            if key == "$datetime":
                try:
                    return datetime.datetime.strptime(
                        value, "%Y-%m-%dT%H:%M:%S.%f")
                except:
                    return datetime.datetime.strptime(
                        value, "%Y-%m-%dT%H:%M:%S")
            elif key == "$objectid":
                return bson.objectid.ObjectId(value)
        return obj


class CoreDataTable(CoreBase):

    def __init__(
            self, length, query, column, fixed_header=True, hide_header=False,
            multi_sort=True, height=None, dense=False, select=True,
            multi_select=True, search=True, per_page=10, page=0, filter=None,
            sort_by=None):
        super().__init__()
        self.column = column
        self.fixed_header = fixed_header
        self.hide_header = hide_header
        self.multi_sort = multi_sort
        self.height = height
        self.dense = dense
        self.select = select
        self.multi_select = multi_select
        self.search = search
        self.length = length
        self.query = query
        if filter is None:
            filter = {}
        self.lookup = {}
        key = None
        for col in self.column:
            self.lookup[col["name"]] = col.get("format", "{}")
            if col.get("key", False):
                if key is not None:
                    raise RuntimeError("multiple keys defined")
                key = col["name"]
        if sort_by is None:
            sort_by = [{"name": key, "ascending": True}]
        sort_by = [(s["name"], 1 if s["ascending"] else -1) for s in sort_by]
        self.pager = CorePager(
            length=self._length, query=self._query, current_page=page,
            per_page=per_page, filter=filter, sort_by=sort_by)
        self.sort_by = sort_by

    async def _length(self, filter):
        # wrapper method around pager, see core4.util.pager
        return await self.length(filter)

    async def _query(self, skip, limit, filter, sort_by):
        # wrapper method around pager, see core4.util.pager
        # this method delivers cell formatting according to the cols definition
        ret = []
        for doc in await self.query(skip, limit, filter, sort_by):
            ndoc = {}
            for k, v in doc.items():
                if k in self.lookup:
                    try:
                        ndoc[k] = self.lookup[k].format(v)
                    except TypeError:
                        self.logger.error("unsupported format string [%s] "
                                          "at [%s]", self.lookup[k], k)
            ret.append(ndoc)
        return ret

    async def post(self):
        """
        Delivers the requested page with

        * ``paging`` - pagination information, see core4.tool.pager
        * ``option`` - data table options
        * ``column`` - data table column definition
        * ``sort`` - data table sort specification
        * ``body`` - list of data table rows (dicts)

        :return: dict
        """
        page = await self.pager.page()
        sort_by = [{"name": n, "ascending": a == 1} for n, a in self.sort_by]
        return dict(
            option=dict(
                fixed_header=self.fixed_header,
                hide_header=self.hide_header,
                multi_sort=self.multi_sort,
                height=self.height,
                dense=self.dense,
                select=self.select,
                multi_select=self.multi_select,
                search=self.search
            ),
            paging=dict(
                per_page=page.per_page,
                page=page.page,
                page_count=page.page_count,
                total_count=page.total_count,
                count=page.count
            ),
            column=self.column,
            sort=sort_by,
            body=page.body
        )

    async def get(self):
        return await self.post()
