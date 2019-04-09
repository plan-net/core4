### Usage

This is a wrapper for v-data-table and accepts all attributes and slots from
 original v-data-table.

```js static
<template>
  <pnbi-datatable
      headline="Datatable plus"
      @search="search = $event"
      :button-label="false"
      customize-label="Columns"
      extend-search="Advanced">

      <!-- primary controls-->
      <!-- secondary slot -->

      <!-- default slot -->
      <pnbi-datatable-plus
        v-if="items.length > 2"
        :items="items" :headers="headers"
        tableIdentifier="123"
        :loading="loading"
        :total-items="totalItems"
        :search="search"
        :pagination.sync="pagination"
        dialog-title="Tabele anpassen"
        dialog-subtitle="Wähle Spalten, die angezeigt werden sollen"
        dialog-closelabel="Schließen"
        dialog-selectalllabel="Alle auswählen"
        dialog-searchlabel="Nach Spalten suchen"
        @updateSearchQuery="onSeachQueryUpdate">
      </pnbi-datatable-plus>

    </pnbi-datatable>
  </template>

  <script>
    import EventBus from 'pnbi-base/src/event-bus'
    export default {
      data() {
        return {
          items: [],
          totalItems: 0,
          loading: true,
          pagination: {
            page: 1,
            rowsPerPage: 10,
            descending: true,
            sortBy: 'age'
          },
          search: null,
          requestObj: {
            filter: {},
            search: null
          },
          newBudget: null,
          projectName: null,
          headers: []
        };
      },
       mounted () {
        EventBus.$on('filterUpdate', this.onFilterUpdate)
        this.getDataFromApi()
          .then(data => {
            this.items = data.tableResponce.items
            this.headers = data.tableResponce.headers
            this.totalItems = data.tableResponce.totalItems
          })
      },
      watch: {
        pagination: function () {
          this.onPaginationEvent()
        }
      },
      methods: {
        // Update filter with this event
        onFilterUpdate (items) {
          this.requestObj.filter = {}
          items.forEach(item => {
            if (item.selectedForSearch) {
              Object.assign(this.requestObj.filter, { [item.value]: item.searchValue })
            }
          })
          this.getDataFromApi()
            .then(data => {
              this.items = data.tableResponce.items
              this.headers = data.tableResponce.headers
              this.totalItems = data.tableResponce.totalItems
            })
        },
        onSeachQueryUpdate (query) {
          // TODO update items
        },
        onPaginationEvent (data, event) {
          this.getDataFromApi()
            .then(data => {
              this.items = data.tableResponce.items
              this.headers = data.tableResponce.headers
              this.totalItems = data.tableResponce.totalItems
            })
        },
        getDataFromApi () {
          this.loading = true
          return new Promise((resolve, reject) => {
            let tableResponce = {}
            let items = []
            while (items.length < 300) {
              items.push({
                name: 'abc123',
                age: Math.floor(Math.random() * 10000) + 1,
                price: 1212349.55,
                value1: 0.33555,
                value2: 'Lorem ipsum dolor sit amet',
                value3: 445566555.778999553,
                value4: Math.floor(Math.random() * 5000) + 1,
                value5: '2018-10-04T00:00:00',
                value6: '2018-10-04T00:00:00',
                value7: 7,
                value8: 8
              })
            }

            const { sortBy, descending, page, rowsPerPage } = this.pagination
            const totalItems = items.length


            // BE sorting
            if (this.pagination.sortBy && items.length > 1) {
              items = items.sort((a, b) => {
                const sortA = a[sortBy]
                const sortB = b[sortBy]

                if (descending) {
                  if (sortA < sortB) return 1
                  if (sortA > sortB) return -1
                  return 0
                } else {
                  if (sortA < sortB) return -1
                  if (sortA > sortB) return 1
                  return 0
                }
              })
            }

            // BE paging
            if (rowsPerPage > 0 && items.length > 1) {
              items = items.slice((page - 1) * rowsPerPage, page * rowsPerPage)
            }

            // collect data
            tableResponce.items = items
            tableResponce.totalItems = totalItems
            tableResponce.headers = [
              { text: 'Name', value: 'name', required: true, default: { '$in': 'user' } },
              { text: 'numbro 2', value: 'age', style: 'numbro.js', format: '0,0', default: { '$eq': 100 } },
              { text: 'currency €', value: 'price', format: '0,0.00', style: 'numbro.js' },
              { text: 'Percent', value: 'value1', format: '0.0%', style: 'numbro.js' },
              { text: 'String', value: 'value2', format: 'DD/MM/YYYY', style: 'moment.js', default: { '$lt': '2019-01-31' } },
              { text: 'Value 3', value: 'value3', format: '6 a', style: 'numbro.js' },
              { text: 'String value', value: 'value4' },
              { text: 'no format & moment', value: 'value5', style: 'moment.js' },
              { text: 'moment', value: 'momentjs', format: 'DD/MM/YYYY', style: 'moment.js' }
            ]

            setTimeout(() => {
              this.loading = false
              resolve({
                tableResponce
              })
            }, 1000)
          })
        }
      }
    }
  </script>
```

### Extend your data object by this attributes

```js static
pagination: {
  page: 1,
  rowsPerPage: 10,
  descending: false,
  sortBy: ''
},
filter: {}
```
Pagination object is used for pagination. Filter object is used for searching in special columns,

Initial is filter object blank. If some columns are defined as defaults, or the user select columns for filtering. The filter object will be filled.

### Listen to EventBus event: filterUpdate

This event is triggered if some chips are changed by user. Import EventBus from pnbi-base

```js static
import EventBus from 'pnbi-base/src/event-bus'
EventBus.$on('filterUpdate', this.onFilterupdate)

onFilterupdate (items) {
  this.requestObj.filter = {}
  items.forEach(item => {
    if (item.selectedForSearch) {
      Object.assign(this.requestObj.filter, { [item.value]: item.searchValue })
    }
  })
  this.fetchData()
}
```
### How to use serverside pagination?

Disabled by default. Enable it by defining folowing props:

Define `total-items` prop. Total-items prop will disable the built-in frontend sorting and pagination. Define `loading` prop. Use Loading prop to display a progress bar while fetching data.

Define listener for events: `@paginationEvent="onPaginationEvent"` this event is fired if user change something in the pagination. So you take new pagination object and make a request to the backend:

```js static
onPaginationEvent (data, event) {
  // update pagination
  this.request.pagination = data
  this.getDataFromApi(this.request)
    .then(data => {
      this.items = data.items
      this.totalItems = data.totalItems
    })
}
```

### Backend API definition

Datatables+ uses numbro.js and moment.js librarys for formatting the values. API developer is responsible for the right number format. All formats are defined in the headers mapping array:

```js static
headers = [
  { text: 'String', value: 'name' },
  { text: 'no format & numbro', value: 'age', style: 'numbro.js'},
  { text: 'currency €', value: 'price', format: '0,0.00', style: 'numbro.js' },
  { text: 'Percent', value: 'value1', format: '0.0%', style: 'numbro.js' },
  { text: 'String', value: 'value2' },
  { text: 'Value 3', value: 'value3', format: '6 a', style: 'numbro.js' },
  { text: 'just number', value: 'value4' },
  { text: 'Start', value: 'value5', format: 'YYYY-MM-DD', style: 'moment.js', 'required': True, 'default': { '$eq': '2019-01-01' } },
  { text: 'End', value: 'value6', format: 'YYYY-MM-DD', style: 'moment.js', 'required': True, 'default': { '$eq': '2019-01-31' } }
]
```
The backend controls all data for datatables.

You can contol wich column is `required` for this table. In example above we have columns "start", "end" ist required defined.
This columns can not be deselected from requesting the data.

You can control what is `default` value for the search inside the column. 

### Backend Request with Filter is like this one

```js static
request: {
	pagination: {},
	filter: {
		name: {
			"$eq": "Alex"
		},
		counter: {
			"$gt": 1 // $gt, $gte
		},
		counter2: {
			"$lt": 10, // $lt, $lte
			"$gt": 5
		},
		value: {
			"$in": "abc" // $lt, $lte
		}
	}
}
```

Filter is a object with objects in structure column: {operator:value}

### Operatoren

**On Strings**

$eq – Matches values that are equal to a specified value.

$in – Matches any of the values specified in an array.

**On Datetime and Number**

$lt – Matches values that are less than a specified value.

$lte	– Matches values that are less than or equal to a specified value.

$gt – Matches values that are greater than a specified value.

$gte – Matches values that are greater than or equal to a specified value.


Always define "style" attribute for numbers. With no style numbro.js number is formated as default number defined by current locale.

### Locales & Languages

For numbro it is two locales by default included: de_DE and en_En. If the browser locale from navigator.language is included in installed locales it would be used. English is default.

Check/Add locales in `numbroLanguages.js`

### Supported formats:

Check the numbro.js website (we use old format)  http://numbrojs.com/old-format.html

Check the momnet.js website
https://momentjs.com/
