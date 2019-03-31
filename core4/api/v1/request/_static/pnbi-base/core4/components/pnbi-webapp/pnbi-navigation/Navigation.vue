<template>
  <v-navigation-drawer
    v-model="sidenavOpen"
    fixed
    clipped
    stateless
    class="core-navigation-container"
    app
  >
    <div class="pt-3">
      <!-- @slot Use this slot for SideNavigation v-list -->
      <v-layout
        class="sidenav"
        row
      >
        <v-flex>
          <v-list
            dense
            class="pb-0"
          >
            <slot></slot>
          </v-list>
        </v-flex>
      </v-layout>
    </div>
    <v-list
      dense
      class="default-routes"
    >
      <v-divider
        class="my-3"
      ></v-divider>

      <v-list-tile :to="{name: 'profile'}">
        <v-list-tile-content>
          <v-list-tile-title>
            Profile
          </v-list-tile-title>
        </v-list-tile-content>
      </v-list-tile>
      <v-list-tile :to="{name: 'privacy'}">
        <v-list-tile-content>
          <v-list-tile-title>
            Privacy Policy
          </v-list-tile-title>
        </v-list-tile-content>
      </v-list-tile>

      <v-list-tile :to="{name: 'imprint'}">
        <v-list-tile-content>
          <v-list-tile-title>
            Imprint
          </v-list-tile-title>
        </v-list-tile-content>
      </v-list-tile>

      <v-list-tile @click="logout()">
        <v-list-tile-content>
          <v-list-tile-title>
            Logout
          </v-list-tile-title>
        </v-list-tile-content>
      </v-list-tile>
    </v-list>
  </v-navigation-drawer>
</template>

<script>
import {
  mapActions
} from 'vuex'
export default {
  name: 'pnbi-navigation',
  mounted () {
    this.$bus.$on('toggleSidenav', this.toggleSidenav)
  },
  props: {
  },
  data () {
    return {
      sidenavOpen: false
    }
  },
  methods: {
    toggleSidenav () {
      this.sidenavOpen = !this.sidenavOpen
    },
    ...mapActions([
      'logout'
    ])
  }
}
</script>

<style scoped>
.default-routes {
  position: fixed;
  bottom: 0;
  width: 100%;
}
</style>
