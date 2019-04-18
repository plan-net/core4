<template>
  <c4-webapp :full-width="true">
    <side-navigation slot="navigation-slot"></side-navigation>
    <div slot="router">
      <transition name="fade" mode="out-in" :duration="{ enter: 200, leave: 300 }">
        <router-view />
      </transition>
    </div>
  </c4-webapp>
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
    }
  }
}
</script>

<style scoped lang="scss">

</style>
