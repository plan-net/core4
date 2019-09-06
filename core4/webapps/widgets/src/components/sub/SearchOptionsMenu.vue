<template>
  <div>
    <v-menu
      open-on-hover
      bottom
      :close-delay="100"
      :close-on-click="false"
      :close-on-content-click="false"
    >
      <template v-slot:activator="{ on }">
        <v-layout
          align-center
          justify-center
          row
          fill-height
          class="append-to-search"
          v-on="on"
        >
          <v-icon>more_vert</v-icon>
        </v-layout>
      </template>

      <v-list>
        <v-list-tile>
          <v-list-tile-action>
            <v-switch
              :value="searchOptions.technical"
              @change="toggle"
              color="primary"
            ></v-switch>
          </v-list-tile-action>
          <v-list-tile-title style="cursor: pointer;" @click="toggle">Show technical widgets</v-list-tile-title>
        </v-list-tile>
      </v-list>
    </v-menu>
  </div>

</template>

<script>
import { mapState } from 'vuex'
export default {
  data () {
    return {

    }
  },
  methods: {
    toggle () {
      if (this.searchOptions.technical === true) {
        this.$store.dispatch('disableTechnicalSearch')
      } else {
        this.$store.dispatch('enableTechnicalSearch')
      }
    }
  },
  computed: mapState([
    'searchOptions'
  ])
}
</script>

<style lang="scss" scoped>
</style>
