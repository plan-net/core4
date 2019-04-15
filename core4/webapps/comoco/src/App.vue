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
import { mapGetters } from 'vuex'
import { getBasePath } from './helper'

export default {
  name: 'CORE4',
  components: {},
  computed: {
    ...mapGetters(['authenticated'])
  },
  watch: {
    authenticated (newValue, oldValue) {
      this.$disconnect()

      if (newValue && newValue !== oldValue) {
        let token = JSON.parse(localStorage.getItem('user'))['token']
        this.$connect(`${getBasePath()}/v1/event?token=${token}`)
      }
    },
    dark (newValue, oldValue) {
      console.log('dark mode', newValue)
      console.log('  new value: ', newValue)
      console.log('  old value', oldValue)
    }
  }
}
</script>

<style scoped lang="scss">

</style>
