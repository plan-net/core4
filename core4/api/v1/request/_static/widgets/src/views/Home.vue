<template>
  <pnbi-page>
    <router-view />
  </pnbi-page>
</template>
<script>
export default {
  name: 'overview',
  components: {
  },
  created () {
    this.$store.dispatch('getWidgets')
    this.$store.dispatch('getBoards')
  },
  mounted () {

  },
  data () {
    return {
    }
  },
  computed: {
  }
}
</script>
<style scoped lang="scss">

</style>
