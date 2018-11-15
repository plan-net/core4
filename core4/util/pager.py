import collections

import math

PageResult = collections.namedtuple("PageResult",
                                    "code message page_count total_count "
                                    "page body count per_page")


class CorePager:
    """
    The paginator features paging with :class:`.CoreRequestHandler`. A request
    handler with pagination must specify two methods:

    #. the query method to collect data for the requested page
    #. the length (total count) of the total data set.

    The :class:`.CorePager` method :meth:`.will then return a
    :class:`PageResult` wich can be handled properly by
    :class:`.CoreRequestHandler` method
    :meth:`.reply <.CoreRequestHandler.reply`.

    **Example:**

    The following example is based on
    :class:`core4.api.v1.request.queue.JobHandler` HTTP method ``GET`` witho no
    parameter. This request returns the active jobs from ``sys.queue`  with
    pagination;:

        class JobHandler(CoreRequestHandler):

            def initialize(self):
                self._collection = {}

            def collection(self, name):
                if name not in self._collection:
                    self._collection[name] = self.config.sys[name].connect_async()
                return self._collection[name]

            async def get(self, _id=None):
                ret = await self.get_listing()
                self.reply(ret)

            async def get_listing(self):

                async def _length(filter):
                    return await self.collection("queue").count_documents(filter)

                async def _query(skip, limit, filter, sort_by):
                    return self.collection("queue").find(
                        filter).skip(skip).sort(*sort_by).limit(limit)

                per_page = int(self.get_argument("per_page", 10))
                current_page = int(self.get_argument("page", 0))
                query_filter = self.get_argument("filter", {})
                sort_by = self.get_argument("sort", [])

                pager = CorePager(
                            per_page=per_page,
                            current_page=current_page,
                            length=_length,
                            query=_query,
                            sort_by=sort_by,
                            filter=query_filter
                        )
                return await pager.page()

    This request handler example has two helper methods. ``.initialize``
    creates a dict ``._collection`` to store asynchronous MongoDB connections
    using :mod:`motor`. The ``.collection`` method instantiated each connection
    to a collection with the special ``.connect_async`` methods. All handlers
    which follow tornado's async paradigm have to use ``.connect_async`'. By
    default, the access via ``.config.sys[name]`` implicetely uses the
    ``.connect'` method using synchronous :mod:`pymongo`.

    The request handlers ``.get`` method forwards the request to async
    ``.get_listing``. This method defines two inline methods ``_length``
    and ``_query``.

    These methods have to process a ``filter`` and a ``skip``, ``limit``, and
    ``sort_by`` attribute respectively.

    After passing the request arguments these methods are
    specified in the ``CorePager`` instance. This object's ``.page`` method
    returns a :class:`.PageResult` named tuple. This object type is
    automatically handled by :class:`.CoreRequestHandler` standard
    :meth:`.reply <.CoreRequestHandler.reply>` method.
    """

    PAGE_ATTR = (
        "per_page", "current_page", "filter", "sort_by")

    def __init__(self, length=None, query=None, *args, **kwargs):
        """
        Instantiates the pager with:

        :param length: callback method processing a ``filter`` attribute. This
                       method is expected to return the total filtered number
                       of records, see :meth:`.length`.
        :param query: callback method processing ``filter``, ``skip``,
                      ``limit``, and ``sort_by`` attribute, see :meth:`.query`.
        :param current_page: of the pager
        :param per_page: number of records per page
        :param filter: dict with :mod:`motor` filter syntax to query MongoDB
                       documents
        :param sort_by: tuple of attribute and sort order (``1`` for ascending,
                        ``-1`` for descending)
        """
        self.__dict__["paging"] = dict(
            per_page=10,
            current_page=0,
            sort_by={},
            filter={},
        )
        self.initialise(*args, **kwargs)
        self._total_count = None
        self._filtered_count = None
        self._length = length or self.length
        self._query = query or self.query

    def __getattr__(self, item):
        if item in self.paging:
            return self.paging[item]
        super().__getattr__(item)

    def __setattr__(self, key, value):
        if key in self.paging:
            self.initialise(**{key: value})
            return
        super().__setattr__(key, value)

    def initialise(self, **kwargs):
        """
        Initialises the following pagination attributes:

        :param per_page: number of records per page
        :param current_page: of the pager
        :param filter: dict with :mod:`motor` query filter
        :param sort_by: tuple of sort attribute and sort order
        """
        for k in kwargs:
            if k in self.PAGE_ATTR:
                self.paging[k] = kwargs[k]
            else:
                self.__dict__[k] = kwargs[k]
        self._total_count = None
        self._filtered_count = None

    @property
    async def total_count(self):
        """
        :return: total number of documents without filter
        """
        if self._total_count is None:
            self._total_count = float(await self._length(filter={}))
        return self._total_count

    @property
    async def filtered_count(self):
        """
        :return: total number of filtered documents
        """
        if self._filtered_count is None:
            self._filtered_count = float(await self._length(
                filter=self.filter))
        return self._filtered_count

    @property
    async def page_count(self):
        """
        :return: total number of pages
        """
        return math.ceil(await self.filtered_count / self.per_page)

    async def page(self, page=None):
        """
        :return: :class:`.PageResult`
        """
        page = page or self.current_page
        self.current_page = page
        if self.current_page < 0:
            self.current_page = await self.page_count + page

        page_count = await self.page_count
        if (page_count == 0 or self.current_page >= page_count):
            return PageResult(
                code=200,
                message="OK",
                page_count=await self.page_count,
                total_count=await self.filtered_count,
                page=self.current_page,
                per_page=self.per_page,
                count=0,
                body=[]
            )
        skip = int(self.current_page * self.per_page)
        limit = int(self.per_page)
        body = await self._query(
            skip, limit, self.filter, self.sort_by)
        return PageResult(
            code=200,
            message="OK",
            page_count=await self.page_count,
            total_count=await self.filtered_count,
            page=self.current_page,
            count=len(body),
            per_page=self.per_page,
            body=body
        )

    async def length(self, filter):
        """
        Needs to be implemented with every pager. The passed filter is
        to be applied.

        :param filter: variant, depends on the pager implementation
        :return: total number (int) of filtered records
        """
        raise NotImplementedError('requires implementation')

    async def query(self, skip, limit, filter, sort_by):
        """
        Needs to be implemented with every pager. The passed ``skip`` attribute
        is the number of records to skip. The ``limit`` attribute is the number
        of records to retrieve. The passed ``filter`` and ``sort_by``
        attributes are to be applied in the search.

        :param skip: number (int) of records to skip
        :param limit: number (int) of records to retrieve
        :param filter: variant, depends on the pager implementation
        :param sort_by: variant, depends on the pager implementation
        :return: list of dict
        """
        raise NotImplementedError('requires implementation')
