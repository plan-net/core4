<template lang="html">

  <v-list>
    <v-radio-group v-model="selected">

      <!-- default -->
      <v-list-tile>
      <v-list-tile-content>
          <v-radio value="$eq">
            <div slot="label">Equals</div>
          </v-radio>
        </v-list-tile-content>
        <v-list-tile-action class="list_action">
          <v-text-field single-line v-model="equalsNumber" @input="setChipText('$eq', equalsNumber)"></v-text-field>
        </v-list-tile-action>
      </v-list-tile>

      <!-- lower -->
      <v-list-tile>
      <v-list-tile-content>
          <v-radio value="$lt">
            <div slot="label">Less than</div>
          </v-radio>
        </v-list-tile-content>
        <v-list-tile-action class="list_action">
          <v-text-field single-line v-model="lessNumber" @input="setChipText('$lt', lessNumber)"></v-text-field>
        </v-list-tile-action>
      </v-list-tile>

      <!-- greater -->
      <v-list-tile>
      <v-list-tile-content>
          <v-radio value="$gt">
            <div slot="label">Greater than</div>
          </v-radio>
        </v-list-tile-content>
        <v-list-tile-action class="list_action">
          <v-text-field single-line v-model="greaterNumber" @input="setChipText('$gt', greaterNumber)"></v-text-field>
        </v-list-tile-action>
      </v-list-tile>

        <div class="pt-3">
          <v-btn flat small primary @click="applyFilter()">Apply</v-btn>
          <!-- <v-btn flat small>Schließen</v-btn> -->
        </div>

    </v-radio-group>
  </v-list>

</template>

<script>
import moment from 'moment'
export default {
  // current item is the advancedSearchItem
  props: ['item'],
  data: function () {
    return {
      date: null,
      normMenuVisible: null,
      lowerMenuVisible: null,
      greaterMenuVisible: null,
      equalsNumber: '',
      lessNumber: '',
      greaterNumber: '',
      internalLocalItem: null
    }
  },
  computed: {
    localItem: {
      get: function () {
        if(this.internalLocalItem === null) {
          let obj = this.$helper.clone(this.item)
          // item with default search value
          if(obj.searchValue) {
            obj.myKey = Object.keys(this.item.searchValue)[0]
            obj.myValue = this.item.searchValue[obj.myKey]
            obj.chipText = "test"
          } else if (obj.default) {
            console.log('default', obj);
            obj.myKey = Object.keys(this.item.default)[0]
            obj.myValue = this.item.default[obj.myKey]
            obj = Object.assign(obj, {searchValue:{[obj.myKey]:obj.myValue} })
          } else {
            obj.myKey = '$eq';
            obj.myValue = ''
            obj = Object.assign(obj, {chipText:'', searchValue:{[obj.myKey]:obj.myValue} })
          }
          return obj
        } else {
          return this.internalLocalItem
        }
      },
      set: function (item) {
        this.internalLocalItem = item
      }
    },
    selected: {
      get: function () {
        return this.localItem.myKey
      },
      set: function (newKey) {
        if(this.item.searchValue) {
          const oldKey = Object.keys(this.item.searchValue)[0]
          this.setChipText(newKey, this.item.searchValue[oldKey])
        }
        this.localItem = Object.assign(this.localItem, {myKey:newKey})
      }
    }
  },
  mounted () {
    this.defineInitChip()
    // this.applyFilter()
  },
  methods: {
    applyFilter () {
      this.$emit('itemUpdate', this.$helper.clone(this.internalLocalItem))
    },
    /**
     * updated item object with some Information from the chipmenu
     * returned item to the parrent
     * @param selectedKey string
     */
    defineInitChip () {
      if(this.localItem.default) {
        let key = Object.keys(this.localItem.searchValue)[0]
        this.setChipText(key, this.localItem.searchValue[key])
        this.applyFilter()
      }
    },
    setChipText (key, value) {
      this.equalsNumber = null
      this.lessNumber = null
      this.greaterNumber = null
      switch(key) {
        case '$eq':
          this.localItem = Object.assign(this.localItem, {chipText:'', searchValue:{[key]:value}})
          this.equalsNumber = value
          break
        case '$lt':
          this.localItem = Object.assign(this.localItem, {chipText:'lower than', searchValue:{[key]:value} })
          this.lessNumber = value
          break
        case '$gt':
          this.localItem = Object.assign(this.localItem, {chipText:'greater than', searchValue:{[key]:value}})
          this.greaterNumber = value
          break
      }
    }
  }
}
</script>

<style lang="css" scoped>
.custom-list {
  padding: 16px;
}
.list_action {
  margin-left: 40px !important;
}
.v-menu__content {
  margin-top: 8px;
}
/deep/ .v-text-field {
  padding-top: 0 !important;
}
</style>
