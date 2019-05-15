<template>
  <c4-webapp :full-width="true" :nav-button-visible="false">
    <side-navigation slot="navigation-slot"></side-navigation>
    <div slot="router">
      <transition name="fade" mode="out-in" :duration="{ enter: 200, leave: 300 }">
        <router-view/>
      </transition>
    </div>
  </c4-webapp>
</template>
<script>
import SideNavigation from '@/components/SideNavigation'

export default {
  name: 'CORE4',
  components: {
    SideNavigation
  },
  computed: {},
  mounted () {
  }
}
</script>
<style lang="scss">

</style>
