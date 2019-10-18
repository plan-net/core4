<template>
  <div>
    <transition name="fade" mode="out-in" :duration="{ enter: 200, leave: 300 }">
      <board v-if="ready"/>
    </transition>
    <widget-manager></widget-manager>
  </div>
</template>

<script>
import WidgetManager from '@/components/WidgetManager'
import Board from '@/components/Board'

export default {
  name: 'boards-home',
  components: {
    WidgetManager,
    Board
  },
  mounted () {

  },
  data () {
    return {}
  },
  computed: {
    ready () {
      return this.$store.getters.ready
    }
  }
}
</script>

<style scoped lang="scss">

</style>
