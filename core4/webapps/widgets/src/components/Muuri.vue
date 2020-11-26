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
        @refresh="refreshItems"
      ></widget>
    </template>
<!--     <div style="height: 1000px;"></div>
    <pre v-for="(item, index) in widgets" :key="index">
      {{item.title}}
    </pre> -->
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
  async mounted () {
    await this.$nextTick()
    // this.setupGrid()
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
  watch: {
    // we watch for widget rsc ids in widgets array to REBUILD grid
    async widgetsHack (newValue, oldValue) {
      this.setupGrid()
    }
  },
  async beforeRouteLeave (to, from, next) {
    this.show = false
    await this.$nextTick()
    next()
  },
  methods: {
    refreshItems () {
      if (this.grid != null) { this.grid.refreshItems().layout() }
    },
    async setupGrid () {
      window.clearTimeout(this.ti)
      this.show = false
      this.ti = window.setTimeout(() => {
        this.show = true
      }, 200)
      if (this.grid != null) {
        this.grid.destroy()
        this.grid.off('dragInit')
        this.grid.off('dragReleaseEnd')
      }
      await this.$nextTick()
      this.grid = new Muuri('.grid', {
        dragEnabled: true,
        dragSortInterval: 100,
        items: '.widget',
        dragHandle: '.handle',
        dragContainer: document.querySelector('#board'),
        layout: {
          fillGaps: true
        }
      })
      let oldIndex
      this.grid.on('dragInit', (item, event) => {
        oldIndex = this.grid.getItems().indexOf(item)
      })
      this.grid.on('dragReleaseEnd', (item) => {
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

  data () {
    return {
      grid: null,
      show: false
    }
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
