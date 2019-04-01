<template lang="html">

  <v-list>
    <v-radio-group v-model="selected">

      <!-- default -->
      <v-list-tile>
      <v-list-tile-content>
          <v-radio value="$eq">
            <div slot="label">Date</div>
          </v-radio>
        </v-list-tile-content>
        <v-list-tile-action class="list_action">
          <v-menu ref="normMenuVisible"
            :close-on-content-click="false"
            v-model="normMenuVisible"
            :return-value.sync="normMenuVisible"
            lazy transition="scale-transition"
            offset-y
            full-width
            min-width="290px">
            <!-- <v-text-field single-line slot="activator" v-model="normDate" label="Default" prepend-icon="event" readonly></v-text-field>
            <v-date-picker no-title v-model="normDate" @input="$refs.lower.save(normDate)" show-current="false"></v-date-picker> -->
            <v-text-field
              slot="activator"
              :value="normDate"
              readonly></v-text-field>
              <v-date-picker no-title v-model="normDate" @input="$refs.normMenuVisible.save(normDate); setChipText('$eq', normDate)" show-current="false"></v-date-picker>
          </v-menu>
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
            <v-menu ref="lowerMenuVisible"
              :close-on-content-click="false"
              v-model="lowerMenuVisible"
              :return-value.sync="lowerMenuVisible"
              lazy transition="scale-transition"
              offset-y full-width
              min-width="290px">
              <v-text-field
                slot="activator"
                :value="lowerDate"
                readonly></v-text-field>
                <v-date-picker no-title v-model="lowerDate" @input="$refs.lowerMenuVisible.save(lowerDate);setChipText('$lt', lowerDate)" show-current="false"></v-date-picker>
            </v-menu>
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
          <v-menu ref="greaterMenuVisible"
            :close-on-content-click="false"
            v-model="greaterMenuVisible"
            :return-value.sync="greaterMenuVisible"
            lazy transition="scale-transition"
            offset-y full-width
            min-width="290px">
            <v-text-field
              slot="activator"
              :value="greaterDate"
              readonly></v-text-field>
              <v-date-picker no-title v-model="greaterDate" @input="$refs.greaterMenuVisible.save(greaterDate);setChipText('$gt', greaterDate)" show-current="false"></v-date-picker>
          </v-menu>
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
      normDate: '',
      lowerDate: '',
      greaterDate: '',
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
            obj.myKey = Object.keys(obj.searchValue)[0]
            obj.myValue = obj.searchValue[obj.myKey]
          } else {
            obj.myKey = '$eq';
            obj.myValue = moment().format('YYYY-MM-DD')
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
        const oldKey = Object.keys(this.item.searchValue)[0]
        this.setChipText(newKey, this.item.searchValue[oldKey])
        this.localItem = Object.assign(this.localItem, {myKey:newKey})
      }
    }
  },
  mounted () {
    this.defineInitChip()
    this.applyFilter()
  },
  methods: {
    applyFilter () {
      this.$emit('itemUpdate', this.$helper.clone(this.internalLocalItem))
      // EventBus.$emit('filterUpdate', this.internalLocalItem.searchValue)
    },
    /**
     * updated item object with some Information from the chipmenu
     * returned item to the parrent
     * @param selectedKey string
     */
    defineInitChip () {
      // TODO check headers from localstorage for saved searchvalues
      let key = Object.keys(this.localItem.searchValue)[0]
      this.setChipText(key, this.localItem.searchValue[key])
    },
    setChipText (key, value) {
      this.normDate = null
      this.lowerDate = null
      this.greaterDate = null
      switch(key) {
        case '$eq':
          this.localItem = Object.assign(this.localItem, {chipText:'', searchValue:{[key]:value}})
          this.normDate = value
          break
        case '$lt':
          this.localItem = Object.assign(this.localItem, {chipText:'lower than', searchValue:{[key]:value} })
          this.lowerDate = value
          break
        case '$gt':
          this.localItem = Object.assign(this.localItem, {chipText:'greater than', searchValue:{[key]:value}})
          this.greaterDate = value
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
