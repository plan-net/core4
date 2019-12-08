#
# Copyright 2018 Plan.Net Business Intelligence GmbH & Co. KG
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Data Table support providing :class:`.CoreDataTable` and
:class:`.CoreDataTableRequest`.
"""

import copy
import datetime
import json
import bson
from pandas import isnull

from core4.base.main import CoreBase
from core4.util.pager import CorePager
from core4.api.v1.request.main import CoreRequestHandler
from core4.base.main import CoreAbstractMixin
import tornado.gen
import tornado.iostream
import pandas as pd


DEFAULT_ALIGN = "left"

def convert(obj):
    """
    Special json hook to parse typed mongodb query. The hook parses

    * datetime objects and
    * objectid objects

    example of a date range filter converting a string into a valid
    datetime object::

        {
            "timestamp": {
                "$gte": {
                    "$datetime": "2014-04-01T00:00:00"
                }
            }
        }

    example of a object id filter converting a string into a valid
    bson object id::

        {
            "_id": {
                "$objectid": "5d8af9cbad70712cbe0521f7"
            }
        }
    """
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

    """
    The ``CoreDataTable`` manages pagination, filtering and sorting and
    specifies the following attributes of the FE/BE component.

    column (list of dict)
       specifies the column order and attributes with ``name`` (str), ``label``
       (str) for the header row, ``key`` (bool) flagging the column identifying
       the  record, ``align`` (str with ``left``, ``right`` and ``center``),
       ``format`` (str) representing the Python formatting, ``nowrap``
       indicating that the text must not be wrapped inside a column,
       ``editable`` (bool) indicating that the user can change the column order
       and/or show/hide  the column, and the ``hide`` attribute itself
    length (callback)
       processes a passed ``filter`` attribute and is supposed to return the
       total number of elements
    query (callback)
       processes the passed ``skip``, ``limit``, ``filter`` and ``sort_by``
       attributes and is supposed to return a of dict representing the records
    fixed-header (bool)
       fixed header at the top of table
    hide-header (bool)
       hide the row header
    height (int)
       set an explicit height of table
    dense (bool)
       decreases the height of rows
    search (bool)
       displays the search bar
    advanced_options (bool)
       display advanced options control
    footer (bool)
       display footer
    info (str)
       general information to be displayed at the table footer. The string can
       contain HTML tags. Set to ``None`` (default) if not information is to be
       displayed.
    action (list of dict)
       specifies an action column with material ``icon`` attribute, ``method``
       of ``GET``, ``POST``, ``PUT``, ``DELETE`` or a non-standard method
       ``FOLLOW`` to replace current location, and ``endpoint``
    page (int)
       changes which page of items is displayed
    per_page (int)
       changes how many items per page should be visible
    filter (str)
       query string to filter data rows
    sort_by (list of dict)
       specifies the sort order with column ``name`` and ``ascending`` (bool)
       property

    The ``CoreDataTable`` component is used by :class:`.CoreDataTableRequest``
    to implement endpoints delivering data tables.
    """
    def __init__(
            self, length, query, column, fixed_header=True, hide_header=False,
            height=None, dense=False, search=True, per_page=10, page=0,
            filter=None, sort_by=None, advanced_options=True, footer=True,
            info=None, action=None):
        super().__init__()
        self.column = copy.deepcopy(column)
        self.fixed_header = fixed_header
        self.hide_header = hide_header
        self.height = height
        self.dense = dense
        self.search = search
        self.length = length
        self.query = query
        if filter is None:
            filter = {}
        self.filter = filter
        self.page = page
        self.sort_by = sort_by
        self.per_page = per_page
        self.advanced_options = advanced_options
        self.footer = footer
        self.info = info
        self.action = action
        self.lookup = {}
        # build format lookup and verify that there is only one key
        key = None
        for i, col in enumerate(self.column):
            self.lookup[col["name"]] = i
            if col.get("key", False):
                if key is not None:
                    raise RuntimeError("multiple keys defined")
                key = col["name"]
        if key is not None and sort_by is None:
            sort_by = [{"name": key, "ascending": True}]
        if sort_by is not None:
            sort_by = [(s["name"], 1 if s["ascending"] else -1)
                       for s in sort_by]
        self.sort_by = sort_by
        self.pager = CorePager(
            length=self._length, query=self._query, current_page=self.page,
            per_page=self.per_page, filter=self.filter, sort_by=self.sort_by)

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
                    if isnull(v):
                        ndoc[k] = "."
                    else:
                        fmt = self.column[self.lookup[k]].get("format", "{}")
                        if callable(fmt):
                            ndoc[k] = fmt(v)
                        else:
                            try:
                                ndoc[k] = fmt.format(v)
                            except (ValueError, TypeError):
                                self.logger.error(
                                    "unsupported format string [%s] at [%s]",
                                    fmt, k)
            ret.append(ndoc)
        return ret

    async def post(self):
        """
        Delivers the requested page with
        
        * ``paging`` - pagination information, see core4.tool.pager, including
          attributes ``page_count``, ``page``, ``count``, ``per_page`` and
          ``total_count``
        * ``option`` - data table options including attributes ``fixed_header``,
          ``hide_header``, ``height``, ``dense``, ``search``,
          ``advanced_options``, ``footer`` and ``info``
        * ``column`` - data table column definition
        * ``action`` - data table actions with icons, methods and endpoints
        * ``sort`` - data table sort specification
        * ``body`` - list of data table rows (dicts)

        :return: dict
        """
        page = await self.pager.page()
        sort_by = [{"name": n, "ascending": a == 1} for n, a in self.sort_by]
        # remove format from response
        column = copy.deepcopy(self.column)
        for col in column:
            if "format" in col:
                del col["format"]
            if "align" not in col:
                col["align"] = DEFAULT_ALIGN
            if "editable" not in col:
                col["editable"] = True
            if "nowrap" not in col:
                col["nowrap"] = False
            if "hide" not in col:
                col["hide"] = False
        return dict(
            option=dict(
                fixed_header=self.fixed_header,
                hide_header=self.hide_header,
                height=self.height,
                dense=self.dense,
                search=self.search,
                advanced_options=self.advanced_options,
                footer=self.footer,
                info=self.info
            ),
            paging=dict(
                per_page=page.per_page,
                page=page.page,
                page_count=page.page_count,
                total_count=page.total_count,
                count=page.count
            ),
            action=self.action,
            column=column,
            sort=sort_by,
            body=page.body
        )

    async def get(self):
        """
        Same as :meth:`.post`
        """
        return await self.post()


class CoreDataTableRequest(CoreRequestHandler, CoreAbstractMixin):
    """
    Inherit from this request handler to deliver data in paginated, nice
    formatted tables.

    Implementing a request requires the definition of the following properties:

    * ``column`` - specifies the order of columns and column attributes (see
      below for further information)
    * ``fixed_header`` - fixes the header at the top of table (defaults to
      ``False``)
    * ``hide_header`` - hides the row header (defaults to ``False``)
    * ``height`` - set an explicit height of table which is required if
      ``fixed_header is True`` (defaults to ``None``)
    * ``dense`` - decreases the height of rows (defaults to ``False``)
    * ``search`` - displays the search bar (defaults to ``True``)
    * ``footer`` - display footer (defaults to ``True``)
    * ``advanced_options`` - display advanced options control (defaults to
      ``True``, see below for further information)
    * ``info`` - general information to be displayed at the table footer. The
      string can contain valid HTML. Set to ``None`` (default) if no information
      is to be displayed.
    * ``action`` - specifies an action column with material ``icon`` attribute,
      ``method`` and the ``endpoint`` (defaults to ``None``, see below for
      further information)
    * ``per_page`` - how many items to be displayed per page (default to 10)
    * ``page`` - which page to display
    * ``filter`` - query filter (see below for further information)
    * ``sort_by`` - sort order (see below for further information)

    Define the default values for these attributes as class properties. The
    following attributes set these as request parameters (URL query parameters
    or body payload):

    * ``dense``
    * all pagination parameters, i..e. ``page``, ``per_page``, ``filter`` and
      ``sort``
    * ``column`` order and visibility

    All datatable request handlers must implement the :meth:`.length` and
    :meth:`.query` method. The :meth:`.length` must process the passed
    ``filter`` (str) and return the total number of records after filtering. The
    :meth:`.query` must process the following set of parameters and returns the
    list of records as dicts with keys *column names* and *column values*.

    * ``skip`` - the number of records to be skipped, determined by ``per_page``
      and ``page`` attribute
    * ``limit`` - the number of records to be returned, determined by
      ``per_page`` attribute
    * ``filter`` - query filter as a plain string. Both methods :meth:`.length`
      and :meth:`.query` must implement appropriate measures for parsing the
      string and filtering the data set
    * ``sort_by`` - list of dict with attributes ``name`` representing the
      column name and ``ascending`` with ``True or False``

    **column definition**

    Each datatable request handler must define the list of columns to be
    rendered. The column specification is a list of dict with the following
    attributes and default values:

    * ``name`` (str) - technical column name
    * ``label`` (str) - column label to be rendered in the header row
    * ``key`` (bool) - flags the row identifier to be userd with datatables
      actions identifying the row to act on. There can only be one column key.
    * ``align`` (str) - cell alignment with valid values ``left``, ``right`` and
      ``center`` (defaults to ``left``).
    * ``format`` (str) - cell formatting using Python modern format syntax,
      defaults to ``{}``.
    * ``nowrap`` (bool) - indicates that the rendering engine must not wrap long
      lines.
    * ``hide`` (bool) - indicates that the column is hidden (defaults to
      ``False``)
    * ``editable`` (bool) - indicates that the user is allowed to change the
      visibility of the column (``hide``) and the column sort order.

    **advanced options**

    If ``advanced_options is True`` then the datatable will provide the
    following features:

    * change column visibility (``hide``) for *editable* columns
    * change column sort order (``column`` list) for *editable* columns
    * change to ``dense`` table format

    **table actions**

    The datatable can be enriched with actions. A list of dict with the
    following attributes specifies actions:

    * ``icon`` - the name of the material icon representing the action
    * ``method`` - the HTTP method ``GET``, ``POST``, ``PUT``, ``DELETE``
      to trigger the action. The non-standard method ``FOLLOW`` will change the
      location if the user triggers the action by clicking the icon.
    * ``endpoint`` - the endpoint to visit if the user triggers the action.

    The ``key`` column is appended to the endpoint to identify the record to act
    on. The value of this column is added to the end of the endpoint with a
    trailing slash (``/``), e.g. ``http://localhost/table1/do_something/4711``,
    with ``http://localhost/table1/do_something`` as the ``endpoint`` and
    ``4711`` as the value of the key column).

    By default ``action is None``.

    **filter**

    The request is supposed to process a query ``filter``. This filter is a
    plain string and has to be processed by methods :meth:`.length` and
    :meth:`.query`. To facililtate json parsing the request handler provides a
    helper method :meth:`.convert_filter`.

    **custom column order and visibility**

    The user can change the column order and visibility for all columns where
    ``editable is True``. The ``GET`` and ``POST`` methods process the request
    parameter ``column`` (listof dict) with an attributes ``name``and ``hide``
    (bool). The list order specifies the column sort order and the ``hide``
    attribute defines which columns to hide.

    **request response**

    The ``GET`` and ``POST`` method of the :class:`.CoreDataTableRequest` return
    a dict with the following attributes:

    * ``option`` - with the current settiings for ``fixed_header``,
      ``hide_header``, ``height``, ``dense``, ``search``, ``advanced_options``,
      ``footer`` and ``info``
    * ``paging`` - with current pagination settings (``page_count``, ``page``,
      ``count``, ``per_page`` and ``total_count``)
    * ``column`` - with column settings, i.e. column sort order and visibility
      (``hide``)
    * ``action`` - as a list of dict with ``icon``, ``method`` and ``endpoint``
    * ``sort`` - with current sort order as a list of dict with ``name`` of the
      column and ``ascending`` specifying the sort order
    * ``body`` - list of list representing the formatted table data in rows
      and columns

    **settings persistance**

    The ``POST`` process stores the following attributes in collection
    ``sys.setting``, document ``_id == "_datatable"``:

    * ``column``
    * ``sort``
    * ``dense``
    * ``per_page``

    This provides persistence of user defined column visibility, column sort
    order and pagination. All future ``GET`` and ``POST`` requests will work
    with these settings. Only ``POST`` will update the settings with an
    appropriate payload.

    The special request parameter ``reset`` (bool) will reset these settings to
    their default values. Please note that these default settings will apply to
    the request with method ``GET``. With ``POST`` the settings will be reset
    for all future requests instead.

    **data download**

    A ``GET`` or ``POST`` request with ``?download=1`` will stream the table
    content to a CSV file. A ``GET`` request with ``?download=1&reset=1`` will
    download the complete datatable and ignores the current column ordering and
    visibility.


    """
    column = None
    per_page = 10
    page = 0
    fixed_header = False
    hide_header = False
    height = None
    dense = False
    search = True
    filter = None
    sort_by = None
    advanced_options = True
    footer = True
    info = None
    action = None

    async def _prepare_table(self, save=False, *args, **kwargs):
        await self.initialise_table()
        reset = self.get_argument("reset", as_type=bool, default=False)
        table_id = self.qual_name().replace(".", "-")
        if not reset:
            doc = await self.config.sys.setting.find_one(
                {"_id": self.user._id}, projection=["_datatable"]
            ) or {}
            if "_datatable" not in doc:
                doc = {"_datatable": {}}
            setting = doc["_datatable"].get(table_id, {})
        else:
            setting = {}

        modified = False

        def _get_arg(name, as_type, keep=False, default=None, **kwargs):
            nonlocal modified
            ret = self.get_argument(
                name, as_type=as_type, default=setting.get(
                    name, getattr(self, name, default), **kwargs))
            if keep and save:
                setting[name] = ret
                modified = True
            return ret

        cdt = CoreDataTable(
            length=self.length,
            query=self.query,
            column=self.column,  # early setting
            fixed_header=self.fixed_header,
            hide_header=self.hide_header,
            height=self.height,
            dense=_get_arg("dense", bool, keep=True),
            search=self.search,
            per_page=_get_arg("per_page", int, keep=True),
            page=_get_arg("page", int, keep=False),
            filter=_get_arg("filter", str, keep=False),
            sort_by=_get_arg("sort", list, keep=True),
            advanced_options=self.advanced_options,
            footer=self.footer,
            info=self.info,
            action=self.action
        )

        # merge user specs with default column
        column = _get_arg("column", list)
        if not reset and column != self.column:
            target_column = []
            required_column = list(range(0, len(cdt.lookup)))
            for req in column:
                if req["name"] in cdt.lookup:
                    cid = cdt.lookup[req["name"]]
                    col = cdt.column[cid]
                    col["hide"] = req.get("hide", col.get("hide", False))
                    target_column.append(col)
                    required_column.remove(cid)
                    cdt.lookup[req["name"]] = len(target_column) - 1
            for cid in required_column:
                target_column.append(cdt.column[cid])
                cdt.lookup[cdt.column[cid]["name"]] = len(target_column) - 1
            cdt.column  = target_column
            # remove formatting from settings store
            setting["column"] = copy.deepcopy(target_column)
            for col in setting["column"]:
                if "format" in col:
                    del col["format"]

        if save and modified:
            if reset:
                await self.config.sys.setting.update_one(
                    {"_id": self.user._id},
                    {"$unset": {"_datatable." + table_id: 1}})
            else:
                await self.config.sys.setting.update_one(
                    {"_id": self.user._id},
                    {"$set": {"_datatable." + table_id: setting}}, upsert=True)
        return cdt

    async def initialise_table(self):
        """
        Overwrite this method for any kind of data preparation.
        """
        pass

    async def _fetch(self, save=False):
        datatable = await self._prepare_table(save)
        download = self.get_argument("download", as_type=str, default=None)
        if download:
            await self._download(datatable)
        else:
            self.reply(
                await datatable.post()
            )

    async def _download(self, datatable):
        pager = datatable.pager
        column = [c for c in datatable.column if not c.get("hide", False)]
        names = [c["name"] for c in column]
        labels = [c["label"] for c in column]
        pager.per_page = self.per_page * 100
        p = 0
        header = True
        pager._query = self.query

        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition',
                        'attachment; filename=' + self.qual_name() + ".csv")
        while True:
            page = await pager.page(p)
            if page.count == 0:
                break
            df = pd.DataFrame(page.body)
            df = df[names]
            df.columns = labels
            try:
                self.write(df.to_csv(header=header, index=False))
                await self.flush()
                self.logger.debug("sent chunk")
            except tornado.iostream.StreamClosedError:
                break
            finally:
                await tornado.gen.sleep(0.000000001)  # 1 nanosecond
            header = False
            p += 1
        self.finish()

    def convert_filter(self, filter):
        """
        Helper method to translate the passed filter (str) into a dict usinig
        json parser. Returns the filter parameter unchanged if this is not
        possible.

        :param filter (str): filter expression
        :return: str or dict
        """
        if filter:
            try:
                filter = json.loads(filter, object_hook=convert)
            except:
                pass
        return filter

    async def post(self):
        """
        Retrieve data table and save all passed parameters as the user's default
        settings.

        Methods:
            POST <endpoint>

        Parameters:
            reset (bool): ignore user defined settings
            dense (bool): render table in dense format
            page (int): page to retrieve, starting with 0
            per_page (int): number of records to retrieve per page
            filter (str): filter to be applied
            sort (list): sort order with column ``name`` and ``ascending``
                (bool)
            column (list): column order with column ``name`` and ``hide`` (bool)
                attribute
            download (bool): stream the complete data table in CSV format

        Returns:
            data element with

            - **paging** (dict):
                pagination information with
                ``page_count`` (int), ``page`` (int), ``count`` (int),
                ``per_page`` (int) and ``total_count`` (int)
            - **option** (dict):
                with ``fixed_header`` (bool),
                ``hide_header`` (bool), ``height`` (int), ``dense`` (bool),
                ``search`` (bool), ``advanced_options`` (bool),
                ``footer`` (bool) and ``info`` (str)
            - **action** (list):
                render last column as action column with
                ``icon`` (str) as the material icon, ``method`` (str) as
                ``GET``, ``POST``, ``PUT``, ``DELETE`` and the non-standard
                action ``FOLLOW`` and ``endpoint`` (str). Is ``None`` if no
                action column is to be rendered.
            - **sort** (list):
                row sort order with ``name`` (str) and
                ``ascending`` (bool)
            - **column** (list):
                column order and definition with ``name``
                (str), ``label`` (str), ``align`` (str with ``left``, ``right``
                or ``center``), ``editable`` (bool), ``hide`` (bool) and
                ``nowrap`` (bool)
            - **body** (list):
                of records with keys as column names and values
                as formatted strings

        Raises:
            401: Unauthorized

        Examples:
            >>> from requests import get, post
            ...
            >>> url = "http://localhost:5001/tests/table"
            ... username = "admin"
            ... password = "hans"
            ...
            ... login = get(
            ...     "http://localhost:5001/core4/api/v1/login?username=%s&password=%s" %(
            ...         username, password))
            ...
            ... # get results with default settings, display available keys
            ... get(url, cookies=login.cookies).json()["data"].keys()
            ... # show pagination
            ... get(url, cookies=login.cookies).json()["data"]["paging"]
            ... # show columns
            ... get(url, cookies=login.cookies).json()["data"]["column"]
            ... # show page 2
            ... post(url, json={"page": 1}, cookies=login.cookies).json()["data"]["paging"]
            {'count': 25,'page': 1,'page_count': 400, 'per_page': 25, 'total_count': 10000.0}
        """
        await self._fetch(True)

    async def get(self):
        """
        HTTP ``GET`` request with same parameters and response as
        :meth:`.post`. This method does not change the user's default settings.
        """
        await self._fetch(False)

    async def length(self, filter):
        raise NotImplementedError

    async def query(self, skip, limit, filter, sort_by):
        raise NotImplementedError
