<template>
  <div class="grid">
    <template v-if="widgets.length === 0">
      <empty />
    </template>
    <template v-else>
      <widget
        v-for="widget in widgets"
        :key="widget.rsc_id"
        :show-handle="showHandle"
        :widget="widget"
      ></widget>
    </template>
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'

import Muuri from 'muuri'
import Widget from '@/components/Widget'
import Empty from '@/components/sub/Empty'
export default {
  components: {
    Widget,
    Empty
  },

  watch: {
    // we watch for widget rsc ids in widgets array to rebuild grid
    async widgetsHack (newValue, oldValue) {
      await this.$nextTick()
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
      let oldIndex
      this.grid.on('dragInit', (item, event) => {
        console.log('oldIndex', item, this.grid.getItems().indexOf(item))
        oldIndex = this.grid.getItems().indexOf(item)
      })
      this.grid.on('dragReleaseEnd', (item) => {
        console.log('newIndex', item, this.grid.getItems().indexOf(item))
        const newIndex = this.grid.getItems().indexOf(item)
        if (newIndex !== oldIndex) {
          this.sortBoard({
            oldIndex,
            newIndex
          })
        }
      })
    },
    ...mapActions('widgets', {
      sortBoard: 'sortBoard'
    })
  },
  computed: {
    ...mapGetters('widgets', [
      'widgets'
    ]),
    showHandle () {
      return this.widgets.length > 1
    },
    widgetsHack () {
      return this.widgets.map(val => val.rsc_id).join('_')
    }
  },
  data () {
    return {
      grid: null,
      show: false
    }
  },
  async mounted () {
    await this.$nextTick()
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
