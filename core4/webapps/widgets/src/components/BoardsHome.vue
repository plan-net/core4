<template>
  <div>
    <transition name="fade" mode="out-in" :duration="{ enter: 200, leave: 300 }">
      <board v-if="ready"/>
    </transition>
    <widget-list />
  </div>
</template>

<script>
import WidgetList from '@/components/WidgetList'
import Board from '@/components/Board'

export default {
  name: 'boards-home',
  components: {
    WidgetList,
    Board
  },
  mounted () {

  },
  data () {
    return {
    }
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
