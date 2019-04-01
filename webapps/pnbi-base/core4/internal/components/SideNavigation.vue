<template>
  <v-layout class="sidenav" row>
    <v-flex>
      <v-list dense class="pb-0" :dark="dark">
        <v-list-tile :to="{name: 'dummy'}">
          <v-list-tile-action>
            <v-icon>loyalty</v-icon>
          </v-list-tile-action>
          <v-list-tile-content>
            <v-list-tile-content class="mandant">
              <span>Navigation Item</span>
            </v-list-tile-content>
          </v-list-tile-content>
        </v-list-tile>
      </v-list>
    </v-flex>
  </v-layout>
</template>
<script>
import {
  mapGetters
} from 'vuex'
export default {
  computed: {
    ...mapGetters([
      'dark'
    ])
  }
}
</script>

<style scoped lang="scss">

</style>
