export default {
  created () {
    // create hash from headers
    const headersStr = JSON.stringify(this.$attrs.headers)
    const headersHash = this.hashCode(headersStr)
    this.localStorageName = `${this.tableIdentifier}${headersHash}`

    const data = window.localStorage.getItem(this.localStorageName)
    if (data == null) {
      window.localStorage.setItem(this.localStorageName, '{}')
      this.saveToLocalStorage()
    }
    this.localStorageHeaders = this.loadFromLocalStorage().headers
  },
  mounted () {
    this.$updateHeaderDom(this.localStorageHeaders)
  },
  computed: {
    localAttrs: {
      get: function () {
        let temp = JSON.parse(JSON.stringify(this.$attrs))
        temp.headers = this.localStorageHeaders.filter(val => val.selected)
        return temp
      },
      set: function (newVal) {
      }
    }
  },
  data () {
    return {
      localStorageName: null,
      customiseDialog: false
    }
  },
  methods: {
    /**
     * Filter localStorageHeaders
     * set header.found true|false for specific display
     */
    filterHeadersBySearch (searchStr) {
      this.localStorageHeaders = this.localStorageHeaders.map(header => {
        if (searchStr === '' || searchStr === null || searchStr === undefined) {
          header.highlight = false
        } else {
          header.highlight = !header.text.toLowerCase().includes(searchStr)
        }
        return header
      })
    },
    /*
    * Toogle all headers on/off
    */
    selectAllHeaders (allHeadersSelected) {
      this.localStorageHeaders = this.localStorageHeaders.map(header => {
        header.selected = allHeadersSelected
        return header
      })
      this.updateHeaders()
    },
    saveToLocalStorage (headers) {
      if (headers == null) {
        headers = this.$attrs.headers.map(val => {
          val.selected = true
          return val
        })
      }
      const storageObject = this.loadFromLocalStorage()
      storageObject.headers = headers
      window.localStorage.setItem(this.localStorageName, JSON.stringify(storageObject))
    },
    loadFromLocalStorage () {
      return JSON.parse(window.localStorage.getItem(this.localStorageName))
    },
    updateHeaders () {
      this.saveToLocalStorage(this.localStorageHeaders)
      this.$updateHeaderDom(this.localStorageHeaders)
    },
    /*
    * Create and return hashCode from string
    * used here for creating id for table
    */
    hashCode (str) {
      return str.split('').reduce((prevHash, currVal) =>
        (((prevHash << 5) - prevHash) + currVal.charCodeAt(0)) | 0, 0)
    },
    $updateHeaderDom (headers) {
      const tbody = this.$el.querySelector('tbody')
      this.$nextTick(function () {
        headers.forEach(function (h, index) {
          // get columns that should be filtered
          const cols = tbody.querySelectorAll(`tr td:nth-child(${index + 1})`)
          // toggle columns
          cols.forEach(c => {
            if (h.selected !== true) {
              c.style.display = 'none'
            } else {
              c.style.display = 'table-cell'
            }
          })
        })
      })
    }
  }
}
