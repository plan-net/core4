<template>
  <div class="grid">
<!--     <pre>{{widgetsHack}}</pre> -->
    <template v-if="widgets === []">
      <empty />
    </template>
    <template v-else-if="show">
      <widget
        :class="{show2}"
        v-for="widget in widgets"
        :key="widget.rsc_id"
        xxxshow-handle="showHandle"
        :data-id="widget.rsc_id"
        :widget="widget"
        @refresh="refreshItems"
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
  mounted () {
    if (this.widgets != null) {
      this.showGrid()
    }
  },
  computed: {
    ...mapGetters('widgets', [
      'widgets'
    ]),
    /*     showHandle () {
      return this.internalWidgets.length > 1
    }, */
    widgetsHack () {
      return this.internalWidgets.map(val => val.rsc_id).join('_')
    },
    internalWidgets () {
      return this.widgets || []
    }
  },
  watch: {
    // we watch for widget rsc ids in widgets array to REBUILD grid
    async widgetsHack (newValue, oldValue) {
      this.showGrid()
    }
  },

  methods: {
    showGrid () {
      window.clearTimeout(this.ti3)
      this.show2 = false
      this.setupGrid()
      this.ti3 = window.setTimeout(() => {
        this.show2 = true
      }, 100)
    },
    refreshItems () {
      if (this.grid != null) { this.grid.refreshItems().layout() }
    },
    async setupGrid () {
      window.clearTimeout(this.ti)
      window.clearTimeout(this.ti2)
      this.show = false
      this.ti = window.setTimeout(() => {
        this.show = true
      }, 33)
      this.ti2 = window.setTimeout(async () => {
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
        this.grid.on('dragReleaseEnd', async (item) => {
          this.grid.synchronize()
          const newSort = this.grid.getItems().map(val => {
            return val._element.dataset.id
          })
          const newIndex = this.grid.getItems().indexOf(item)
          if (newIndex !== oldIndex) {
            this.sortBoard({
              oldIndex,
              newIndex,
              newSort
            })
            await this.$nextTick()
          }
        })
      }, 100)
    },
    ...mapActions('widgets', {
      sortBoard: 'sortBoard'
    })
  },

  data () {
    return {
      grid: null,
      show: false,
      show2: false
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
.widget {
  transition: opacity 0.25s ease-in-out;
  opacity: 0;
  &.show2{
    opacity:1
  }
}
</style>
