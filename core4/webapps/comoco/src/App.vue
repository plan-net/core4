<template>
  <pnbi-webapp :full-width="true">
    <side-navigation slot="navigation-slot"></side-navigation>
    <div slot="router">
      <transition name="fade" mode="out-in" :duration="{ enter: 200, leave: 300 }">
        <router-view />
      </transition>
    </div>
  </pnbi-webapp>
</template>

<script>
import SideNavigation from '@/components/SideNavigation'
import { mapGetters } from 'vuex'
import { getBasePath } from './helper'

const WS_BASE_PATH = getBasePath()

export default {
  name: 'CORE4',
  components: {
    SideNavigation
  },
  computed: {
    ...mapGetters(['authenticated'])
  },
  watch: {
    authenticated (newValue, oldValue) {
      // ToDo: check login/logout behavior

      if (newValue && newValue !== oldValue) {
        this.$disconnect()

        let token = JSON.parse(localStorage.getItem('user'))['token']
        this.$connect(`${WS_BASE_PATH}/v1/event?token=${token}`)
      }
    }
  }
}
</script>

<style scoped lang="scss">

</style>
