<template>
  <c4-page>
    <router-view />
  </c4-page>
</template>
<script>
export default {
  name: 'overview',
  created () {
    this.$store.dispatch('getWidgets')
    this.$store.dispatch('getBoards')
  }
}
</script>
<style scoped lang="scss">
</style>
