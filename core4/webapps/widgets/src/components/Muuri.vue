<template>
  <div class="grid">
    <widget
      v-for="widget in widgets"
      :key="widget.rsc_id"
      :widget="widget"
    />
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

import Muuri from 'muuri'
import Widget from '@/components/Widget'
export default {
  components: {
    Widget
  },

  watch: {
    async widgets (newValue, oldValue) {
      this.setupGrid()
    }
  },
  async beforeRouteLeave (to, from, next) {
    this.show = false
    await this.$nextTick()
    next()
  },
  methods: {
    setupGrid () {
      window.clearTimeout(this.ti)
      this.show = false
      this.ti = window.setTimeout(() => {
        this.show = true
      }, 200)
      if (this.grid != null) {
        this.grid.destroy()
        this.grid.off('dragReleaseEnd')
      }
      this.grid = new Muuri('.grid', {
        dragEnabled: true,
        dragSortInterval: 100,
        items: '.widget',
        dragHandle: '.handle',
        dragContainer: document.querySelector('#board'),
        layout: {
          fillGaps: true
        },
        dragStartPredicate: {
          distance: 10,
          delay: 100
        },
        dragReleaseDuration: 400,
        dragReleseEasing: 'ease'
      })
      this.grid.on('dragInit', (item, event) => {
        console.log('oldIndex', item, this.grid.getItems().indexOf(item))
      })
      this.grid.on('dragReleaseEnd', (item) => {
        console.log('newIndex', item, this.grid.getItems().indexOf(item))
      })
    }
  },
  computed: {
    ...mapGetters('widgets', [
      'widgets'
    ])
  },
  data () {
    return {
      grid: null,
      show: false
    }
  },
  mounted () {
    this.setupGrid()
  }

}
</script>

<style lang="scss" scoped>
.grid {
  position: relative;
  max-width: 100%;
  box-sizing: content-box;
}
</style>
