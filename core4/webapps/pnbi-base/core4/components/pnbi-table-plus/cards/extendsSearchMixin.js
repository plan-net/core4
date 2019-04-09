export default {
  mounted () {
    // register event listener
    this.$bus.$on('extendSearchEvent', this.onExtendSearchEvent)
    this.$bus.$on('updateChip', this.onUpdateChipEvent)
    this.enableDefaultItemsInAdvancedSearch()
  },
  computed: {
    itemsForAdvancedSearch: {
      get () {
        return this.items.filter(header => header.selectedForSearch)
      },
      set (item) {
        this.items = this.items.map(val => {
          if (val.value === item.value) {
            val = item
          }
          return val
        })
      }
    }
    // _items: {
    //   get () { return this.items },
    //   set (item) {
    //     this._items = this._items.map(val => {
    //       if (val.value === item.value) {
    //         val = item
    //       }
    //       return val
    //     })
    //   }
    // }
  },
  watch: {
    dialog (val) {
      if (!val) return
      requestAnimationFrame(() => {
        this.$refs.focus.focus()
      })
    }
  },
  methods: {
    onUpdateChipEvent (item) {
      this.itemsForAdvancedSearch = this.itemsForAdvancedSearch.map(val => {
        if (val.value === item.value) {
          val = item
        }
        return val
      })
      // TODO close current menu .headline
    },
    /**
     * Open menu for edit the avancedSearchTerm
     * @param item that should be changed
     */
    openChipDialog (item) {
      item.editDialog = !item.editDialog
    },
    /**
     * Remove chip
     * @param item that should be removed
     */
    onChipClose (item) {
      this.itemsForAdvancedSearch = this.itemsForAdvancedSearch.filter(header => {
        if (header.value === item.value) {
          header.selectedForSearch = false
        }
        return header
      })
    },
    /**
     * Show dialog for advanced search
     */
    onExtendSearchEvent () {
      this.searchPlusDialogVisible = !this.searchPlusDialogVisible
    },
    /**
     * Enable defaults that are delivered over advanced-defaults prop
     */
    enableDefaultItemsInAdvancedSearch () {
      if (this.itemsDefault === null) {
        return true
      }
      this.itemsDefault.filter(defaultItem => {
        // this._items = this.items.filter(headerItem => {
        //   let key = Object.keys(headerItem)[0]
        //   if (header.value === key) {
        //     header.selectedForSearch = true
        //     header.advancedSearchItem = item[key]
        //   }
        //   return headerItem
        // })
        // return defaultItem
      })
      // this.$emit('update:items', this._items)
    }
  }
}
