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
    console.log('init c4.widgets')
  }
}
</script>
