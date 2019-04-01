<template lang="html">
  <pnbi-dialog :title="dialogTitle" :open="dialogVisible" @close="dialogVisible=false" width="500">
    <div slot="dialog-content">
      <v-list>
        <v-subheader>
          {{dialogSubtitle}}
        </v-subheader>

        <v-list-tile>
          <v-list-tile-content>
              <v-checkbox :label="dialogSelectalllabel" @change="$emit('selectAllHeaders', allHeadersSelected)" v-model="allHeadersSelected"
                style="align-items:center">
              </v-checkbox>
            </v-list-tile-content>
            <v-list-tile-action>
              <v-text-field
                clearable
                class="pnbi-search"
                append-icon="search"
                flat full-width
                :label="dialogSearchlabel"
                v-model="searchStr">
              </v-text-field>
          </v-list-tile-action>
        </v-list-tile>

        <v-divider></v-divider>

        <draggable class="list-scrolWrapper" :list="localStorageHeaders" @start="drag=true" @end="saveHeaders($event)">
          <v-list-tile v-for="header in localStorageHeaders" :key="header.text" :class="{'highlighted': header.highlight}">
            <v-list-tile-content>
              <v-checkbox :label="header.text" @change="saveHeaders()" v-model="header.selected" :value="header.selected"
                style="align-items:center">
              </v-checkbox>
            </v-list-tile-content>

            <v-list-tile-action class="text-sm-right">
              <v-icon color="grey lighten-1">drag_indicator</v-icon>
            </v-list-tile-action>

          </v-list-tile>
        </draggable>
      </v-list>
    </div>

    <div slot="dialog-actions">
      <v-btn dark color="primary" @click="dialogVisible = false" flat>
        {{dialogCloselabel}}
      </v-btn>
    </div>
  </pnbi-dialog>
</template>

<script>
import draggable from 'vuedraggable'
export default {
  name: 'customiseDialog',
  components: {
    draggable
  },
  props: {
    /**
     * Items for displaying in an list
     */
    localStorageHeaders: {
      type: Array,
      default: null
    },
    /**
     * Defined the dialog title for customised dialog.
     */
    dialogTitle: {
      type: String,
      default: 'Customise table'
    },
    /**
     * Defined the dialog subtitle for customised dialog.
     */
    dialogSubtitle: {
      type: String,
      default: 'Select visible columns'
    },
    /**
     * Defined the label for selecting all headers in dialog
     */
    dialogSelectalllabel: {
      type: String,
      default: 'Select all'
    },
    /**
     * Label for search placeholder inside of dialog
     */
    dialogSearchlabel: {
      type: String,
      default: 'Search'
    },
    /**
     * Defined label for dialog close button
     */
    dialogCloselabel: {
      type: String,
      default: 'Close'
    },
  },
  data: function () {
    return {
      dialogVisible: false,
      searchStr: null,
      allHeadersSelected: true
    }
  },
  mounted () {
    this.$bus.$on('openCustomizeDialog', this.showDialog)
  },
  beforeDestroy(){
    this.$bus.$off('openCustomizeDialog', this.showDialog)
  },
  methods: {
    showDialog () {
      this.dialogVisible = true
    },
    saveHeaders() {
      this.$emit('saveHeaders')
    },
  },
  watch: {
    searchStr: function () {
      this.$emit('filterHeadersBySearch', this.searchStr)
    }
  },
}
</script>

<style lang="scss" scoped>
.highlighted {
  opacity: 0.3;
}
.list-scrolWrapper {
  max-height: 350px;
  overflow-y: scroll;
}
/deep/ .v-label {
  font-size: 16px;
}
</style>
