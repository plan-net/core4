<template lang="html">
  <v-card>
    <v-card-text>
      <v-text-field
        autofocus
        ref="focus"
        label="Includes ..."
        :value="computedItem.searchValue.$in"
        @input="handleInput"
        @keyup.enter="applyFilter">
      </v-text-field>
      <!-- <p class="caption">Verknüpfe die Suche in der Spalte "{{item.text}}" mit Suchen aus anderen Spalten.</p> -->
    </v-card-text>
    <v-card-actions>
      <v-btn flat small primary @click="applyFilter">Apply</v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
export default {
  props: ['item'],
  // define initial value
  mounted: function () {
    if(this.item.searchValue === undefined) {
      this.handleInput('')
    }
  },
  data: function () {
    return {
      internalItem: null
    }
  },
  computed: {
    computedItem: {
      get: function () {
        if (this.internalItem === null) {
          if(!this.item.searchValue) {
            Object.assign(this.item, { searchValue: { '$in': '' } })
          }
          return this.$helper.clone(this.item)
        } else {
          return this.internalItem
        }
      },
      set: function (item) {
        this.internalItem = item
      }
    }
  },
  methods: {
    handleInput (val) {
      this.computedItem = Object.assign(this.computedItem, { searchValue: { '$in': val } })
    },
    applyFilter () {
      this.$emit('itemUpdate', this.computedItem)
    }
  }
}
</script>

<style>
.custom-list {
  padding: 16px;
}
.list_action {
  margin-left: 40px !important;
}
.v-menu__content {
  margin-top: 8px;
}
</style>
