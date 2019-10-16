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


class CoreDataTableMixin:

    def init_datatable(self, length, query, fixed_header=True,
                       hide_header=False, multi_sort=True, height=None,
                       dense=False, select=True, multi_select=True, search=True,
                       per_page=10, page=0, filter=None):
        args = dict(
            length=length,
            query=query,
            fixed_header=self.get_argument("fixed_header", bool,
                                           default=fixed_header),
            hide_header=self.get_argument("hide_header", bool,
                                          default=hide_header),
            multi_sort=multi_sort,
            height=height,
            dense=self.get_argument("dense", bool, default=dense),
            select=select,
            multi_select=multi_select,
            search=search,
            per_page=self.get_argument("per_page", int, default=per_page),
            page=self.get_argument("page", int, default=page),
            filter=self.get_argument("filter", dict, default=filter or {},
                                     dict_decode=convert),
        )
        return CoreDataTable(**args)


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
        return await self.length(filter)

    async def _query(self, skip, limit, filter, sort_by):
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
            filter=self.pager.filter,
            column=self.column,
            sort=sort_by,
            body=page.body
        )

    async def get(self):
        return await self.post()

