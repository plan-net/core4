<template>
  <div v-resize.quiet="onResize">
    <template v-if=noBoards>
      <div class="text-xs-center pt-5">

        <v-tooltip>
          <v-btn
            @click="$bus.$emit('edit-board-name')"
            color="primary"
            large
            dark
            fab
            slot="activator"
            fixed
          >
            <v-icon>add</v-icon>
          </v-btn>
          <span>Create a board</span>
        </v-tooltip>
      </div>
    </template>
    <template v-else>
      <v-layout>
        <h1 class="headline mb-4 pt-2">{{name}}
          <v-tooltip top>
            <v-btn
              @click="$bus.$emit('edit-board-name')"
              slot="activator"
              flat
              icon
              class="mt-0 pt-0"
              color="grey"
            >
              <v-icon>edit</v-icon>
            </v-btn>
            <span>Change board name</span>
          </v-tooltip>
        </h1>
      </v-layout>
    </template>

    <drop
      class="drop"
      @drop="onDrop"
      :class="{ 'over':over }"
      @dragover="onOver"
      @dragleave="over = false"
    >
      <!-- :layout.sync="internalWidgets" -->
      <howto v-if="internalWidgets && internalWidgets.length === 0"></howto>
      <dnd-grid-container
        v-else-if="internalWidgets"
        v-bind:layout="internalWidgets"
        v-on:update:layout="internalWidgets = $event"
        :cell-size="cellSize"
        :max-column-count="maxColumnCount"
        :max-row-count="maxRowCount"
        :margin="margin"
        :bubble-up="bubbleUp"
      >
        <dnd-grid-box
          v-for="widget in internalWidgets"
          :box-id="widget.id"
          :key="widget.id"
          drag-selector=".v-card__title"
        >
          <v-card>
            <v-card-text>
              <v-icon @click="removeFromBoard(widget._id)" ripple small class="remove-icon grey--text">clear</v-icon>
              <div class="text-xs-center" style="padding-top: 54px;">
                <v-tooltip top>
                  <v-btn
                    @click="$router.push({ name: 'widget', params: { widgetId: widget._id } })"
                    slot="activator"
                    icon
                    large
                    ripple
                  >
                    <v-icon
                      color="grey"
                      large
                    >open_in_new</v-icon>
                  </v-btn>
                  <span>Open widget</span>
                </v-tooltip>
                <v-tooltip top>
                  <v-btn
                    @click="$router.push({ name: 'help', params: { widgetId: widget._id } })"
                    icon
                    slot="activator"
                    large
                    ripple
                  >
                    <v-icon
                      color="grey"
                      large
                    >help</v-icon>
                  </v-btn>
                  <span>Help</span>
                </v-tooltip>
              </div>
            </v-card-text>
            <v-card-title>
              <v-layout column>
                <span>{{widget.title}}</span>
                <small class="grey--text">{{widget.qual_name}}</small>
              </v-layout>
              <v-spacer></v-spacer>
              <v-icon class="widget-drag-icon white--text">drag_indicator</v-icon>
            </v-card-title>
          </v-card>
        </dnd-grid-box>
      </dnd-grid-container>
    </drop>
  </div>
  <!-- v-if="widget.endpoint && isMouseDown === false" -->
</template>
<script>
import { mapGetters, mapActions } from 'vuex'
// import Container and Box components
import { Container, Box } from '@dattn/dnd-grid'
// minimal css for the components to work properly
import '@dattn/dnd-grid/dist/dnd-grid.css'
import Howto from '@/components/Howto.vue'
const lodash = require('lodash')

export default {
  name: 'board',
  components: {
    DndGridContainer: Container,
    DndGridBox: Box,
    Howto
  },
  mounted () {

  },
  watch: {

  },
  data () {
    return {
      elWidth: (this.$el || document.querySelector('body')).offsetWidth,
      isMouseDown: false,
      over: false,
      cellSize: {
        w: 360,
        h: 260
      },
      oldSortOrder: null,
      maxColumnCount: 4,
      maxRowCount: Infinity,
      bubbleUp: true,
      margin: 20
    }
  },

  computed: {
    noBoards () {
      return !this.activeBoard && !this.name
    },
    ...mapGetters(['activeBoard']),
    name () {
      return (this.activeBoard || {}).name
    },
    internalWidgets: {
      // getter
      get: function () {
        if (this.activeBoard && this.activeBoard.widgets) {
          const offset = Math.floor(this.elWidth / this.cellSize.w)
          const tmp = this.activeBoard.widgets.map((id, index) => {
            return Object.assign({},
              this.$store.getters.widgetById(id), {
                id,
                position: {
                  x: index % offset,
                  y: Math.floor(index / offset),
                  w: 1,
                  h: 1
                }
              })
          })
          return tmp
        }
        return null
      },
      // setter
      set: function (newValue) {
        this.$nextTick(function () {
          if (this.isMouseDown === false) {
            const sortOrder = newValue.map(val => val._id)
            this.$store.dispatch('updateBoardWidgets', sortOrder)
          }
        })
      }
    }
  },
  methods: {
    mouseDown () {
      this.isMouseDown = true
    },
    mouseUp () {
      this.isMouseDown = false
    },
    onResize: lodash.debounce(function () {
      this.elWidth = (this.$el || document.querySelector('body')).offsetWidth
    },
    750),
    ...mapActions(['addToBoard', 'removeFromBoard']),
    onOver (item) {
      this.over = true
    },
    onDrop (item) {
      this.addToBoard(item.widgetId)
    }
  }
}
</script>

<style scoped lang="scss">
.remove-icon{
  position: absolute;
  top: 5px;
  right: 8px;
  opacity: .5;
}
.headline {
  text-transform: initial;
}
/deep/ .v-card__text {
  padding: 0;
  height: calc(100% - 68px);
  iframe {
    background-color: #fff;
    width: 100%;
    height: 100%;
  }
}
/deep/ .v-card__title {
  span,
  small {
    white-space: nowrap;
    max-width: 300px;
    overflow: hidden;
    text-overflow: ellipsis;
    pointer-events: none;
    user-select: none;
  }
  background-color: var(--v-secondary-lighten2);
  font-weight: 700;
  text-transform: uppercase;
  color: #fff;
  cursor: move;
}
.widget-drag-icon {
  cursor: move;
  position: relative;
  right: -10px;
  opacity: 0.5;
  pointer-events: none;
}
.drop {
  width: 100%;
  height: 100%;
  min-height: 800px;
}
.dnd-grid-box {
  .v-card {
    height: 100%;
  }
}
.dnd-grid-container {
}
</style>
<style scoped lang="scss">
.theme--dark {
  /deep/ .v-card__title {
    background-color: var(--v-secondary-lighten2);
  }
}
.theme--light {
  /deep/ .v-card__title {
    background-color: darken(#fff, 10);
    color: var(--v-secondary-lighten2);
  }
  .widget-drag-icon {
    opacity: 1;
    color: rgba(0, 0, 0, 0.87) !important;
  }
}
</style>
