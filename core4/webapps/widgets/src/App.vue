<template>
  <c4-webapp :full-width="true">
    <side-navigation slot="navigation-slot"></side-navigation>
  </c4-webapp>
</template>

<script>
import SideNavigation from '@/components/SideNavigation'
export default {
  components: {
    SideNavigation
  },
  mounted () {
    console.info('init c4n')
    /*     window.addEventListener('message', (e) => {
      console.log(e.source)
    }, false) */
  }
}
</script>
