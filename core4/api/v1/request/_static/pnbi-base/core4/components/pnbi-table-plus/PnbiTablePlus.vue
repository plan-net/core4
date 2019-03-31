<template>

  <div class="pnbi-datatable" ref="toolbar">

    <!-- customise dialog here -->
    <customise-dialog
      :localStorageHeaders="localStorageHeaders"
      @saveHeaders="updateHeaders()"
      @filterHeadersBySearch="filterHeadersBySearch($event)"
      @selectAllHeaders="selectAllHeaders($event)"></customise-dialog>

    <!-- Advanced search -->
    <extend-search-dialog
      :items="localStorageHeaders"
      @updateItems="updateItems($event)"></extend-search-dialog>

    <!-- Toolbar with chips -->
    <chips
      :items="localStorageHeaders"
      @updateItems="updateItems($event)"></chips>

    <v-data-table v-bind="localAttrs" :pagination.sync="compPagination">
      <template slot="items" slot-scope="props">
        <tr @click="$emit('open-row', props.item)">
          <td v-for="(key, value, index) in localStorageHeaders" :key="index" nowrap class="tdcell" :title="props.item[key.value]"
            :class="{'text-xs-right': isNumber(props.item[key.value], key.value)}">
            {{props.item[key.value] | customFormatter(key)}}
          </td>
        </tr>
      </template>

      <!-- TODO enable custom empty state
      <template slot="no-results">
        <pnbi-empty text="No data to display"></pnbi-empty>
      </template> -->

    </v-data-table>
  </div>

</template>

<script>
import EventBus from 'pnbi-base/src/event-bus'
import UpdateAndSaveMixin from './updateAndSaveMixin.js'
import is from 'is'
import Chips from './cards/Chips'
import CustomiseDialog from './dialogs/CustomiseDialog'
import ExtendSearchDialog from './dialogs/ExtendSearchDialog'
import _debounce from 'lodash.debounce'
export default {
  name: 'pnbi-datatable-plus',
  components: {
    Chips,
    CustomiseDialog,
    ExtendSearchDialog
  },
  mixins: [UpdateAndSaveMixin],
  props: {
    /**
     * Uniq identifier for table.
     * used for saving the customised settings in localstorage
     */
    tableIdentifier: {
      type: String,
      required: true,
      default: 'default'
    },
    /**
     * Default columns that are enabled for advanced search
     */
    filter: {
      type: Array,
      default: null
    }
  },
  methods: {
    /*
    * Send the API request with a debounce of 1000ms
    *
    */
    sendFilterUpdateEvent: _debounce(function send (items) {
      const visibleItems = items.filter(item => item.selectedForSearch)
      const enabledForSearchItems = items.filter(item => item.searchValue)
      console.log('--', visibleItems, enabledForSearchItems)
      this.localStorageHeaders = items
      this.saveToLocalStorage(this.localStorageHeaders)
      if (visibleItems.length === enabledForSearchItems.length) {
        EventBus.$emit('filterUpdate', this.$helper.clone(this.localStorageHeaders))
      }
    }, 1000),
    updateItems (items) {
      this.sendFilterUpdateEvent(items)
    },
    isNumber (val, key) {
      const isNumber = is.number(val)
      if (isNumber) {
        this.localAttrs.headers = this.localAttrs.headers.map(header => {
          if (header) {
            if (header.value === key) {
              header.align = 'right'
            }
            return header
          }
        })
      }
      return isNumber
    },
    onSearchQueryEvent (query) {
      this.$emit('updateSearchQuery', query)
    }
  },
  computed: {
    compPagination: {
      get: function () {
        let temp = Object.assign({}, this.localAttrs.pagination)
        // if(temp.sortBy = '') {
        //   temp.sortBy = 'age'
        // }
        return temp
      },
      set: function (pagination) {
        this.$emit('update:pagination', pagination)
        this.$nextTick(function () {
          this.$updateHeaderDom(this.localStorageHeaders)
        })
      }
    }
  },
  data: function () {
    return {
      debounced: null,
      drag: null,
      searchPlusToolbarVisible: false,
      searchPlusDialogVisible: false,
      localStorageHeaders: []
    }
  }
}
</script>

<style lang="scss" scoped>
  .tdcell {
    max-width: 350px;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  /deep/ .v-input__control {
    padding: 0 !important;
    min-height: 32px !important;
  }
  /deep/ .pnbi-search .v-input__slot {
    background: rgba(0,0,0,.1);
    margin: 0 !important;
  }
  /deep/ .v-text-field__details {
    margin-bottom: 0 !important;
  }
  .card-wrapper {
    padding: 8px;
  }
  .caption {
    max-width: 15em;
    margin-bottom: 0;
    color: #7a869a;
  }
</style>
