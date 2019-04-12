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

function getBasePath () {
  if (window.location.href.includes('http')) {
    // index.html
    return window.APIBASE_CORE.replace('http:', 'ws:')
  }

  console.error(`incorrect network protocol ${window.location.href}`)

  return `ws://${window.location.host}/core4/api`
}

export default {
  name: 'CORE4',
  components: {},
  computed: {
    ...mapGetters(['authenticated'])
  },
  watch: {
    authenticated (newValue, oldValue) {
      // ToDo: check login/logout behavior
      this.$disconnect()

      if (newValue && newValue !== oldValue) {
        let token = JSON.parse(localStorage.getItem('user'))['token']
        this.$connect(`${getBasePath()}/v1/event?token=${token}`)
      }
    }
  }
}
</script>

<style scoped lang="scss">

</style>
