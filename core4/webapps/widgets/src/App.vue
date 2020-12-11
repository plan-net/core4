<template>
  <c4-webapp :full-width="true" :hide-hamburger="false">
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
  }
}
</script>
