<template>
  <!-- https://github.com/kutlugsahin/smooth-dnd -->
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
      :class="{ 'over-board': over }"
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
          :key="widget.id"
          :box-id="widget.id"
          drag-selector=".v-card__title"
        >
          <v-card :class="{'over': widget.$over}">
            <v-layout class="icon-container">
              <v-tooltip top>
                <v-btn
                  @click="openInNew(widget)"
                  icon
                  small
                  slot="activator"
                  ripple
                >
                  <v-icon
                    small
                    color="grey"
                  >open_in_new
                  </v-icon>
                </v-btn>
                <span>Open widget in new tab</span>
              </v-tooltip>
              <v-tooltip top>
                <v-btn
                  @click="$router.push({ name: 'help', params: { widgetId: widget.rsc_id } })"
                  icon
                  small
                  slot="activator"
                  ripple
                >
                  <v-icon
                    small
                    color="grey"
                  >help
                  </v-icon>
                </v-btn>
                <span>Open widget help page</span>
              </v-tooltip>
              <v-spacer></v-spacer>
              <v-tooltip top>
                <v-btn
                  @click="removeFromBoard(widget.rsc_id || widget.id)"
                  icon
                  small
                  slot="activator"
                  ripple
                >
                  <v-icon
                    ripple
                    small
                    class="grey--text"
                  >remove_circle_outline
                  </v-icon>
                </v-btn>
                <span>Remove widget from board</span>
              </v-tooltip>
            </v-layout>
            <template v-if="widget.endpoint">

              <a
                :href="widget.endpoint.enter_url"
                @click.prevent="()=>{}"
              >
                <v-card-text
                  @click="$router.push({ name: 'enter', params: { widgetId: widget.rsc_id } })"
                  :alt="widget.endpoint.enter_url"
                >

                  <div
                    class="text-xs-center"
                    style="padding-top: 54px;"
                  >
                    <v-tooltip top>
                      <v-icon
                        class="open-widget-icon"
                        slot="activator"
                        color="grey"
                      >{{widget.icon}}
                      </v-icon>
                      <span>Open widget</span>
                    </v-tooltip>

                  </div>
                </v-card-text>
              </a>
            </template>
            <v-card-title>
              <v-layout column>
                <span>{{widget.title}}</span>
                <small class="grey--text tooltip">{{widget.qual_name}}</small>
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
import { mapActions, mapGetters } from 'vuex'
// import Container and Box components
import { Box, Container } from '@dattn/dnd-grid'
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
    this.$nextTick(function () {
      this.onResize()
    })
  },
  methods: {
    openInNew (widget) {
      let path = null
      if (widget.target === 'blank') {
        path = widget.enter_url || widget.endpoint.enter_url
      } else {
        path = '/#/enter/' + widget.rsc_id
      }
      window.open(path, '_blank')
    },
    /*    mouseDown () {
        this.isMouseDown = true
      },
      mouseUp () {
        this.isMouseDown = false
      }, */
    onResize: lodash.debounce(function () {
      this.elWidth = (this.$el || document.querySelector('body')).offsetWidth
      if (this.widgetListOpen) {
        this.elWidth -= 360 - 15 // wide List document.querySelector('.widget-list')).offsetWidth
      } else {
        this.elWidth -= 60 - 15// miniVariant
      }
    },
    750),
    ...mapActions(['addToBoard', 'removeFromBoard']),
    onOver (item) {
      this.over = true
    },
    onDrop (item) {
      this.addToBoard(item.widgetId)
    }
  },
  beforeDestroy () {
    /*     this.$bus.$off('mouseOver')
      this.$bus.$off('mouseOver') */
  },
  data () {
    return {
      elWidth: (this.$el || document.querySelector('body')).offsetWidth,
      isMouseDown: false,
      over: false,
      cellSize: {
        w: 360,
        h: 250
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
    ...mapGetters(['activeBoard', 'widgetListOpen']),
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
            const sortOrder = newValue.map(val => val.rsc_id)
            this.$store.dispatch('updateBoardWidgets', sortOrder)
          }
        })
      }
    }
  }
}
</script>

<style scoped lang="scss">
  .list-enter-active, .list-leave-active {
    transition: all 1s;
  }

  .list-enter, .list-leave-to /* .list-leave-active below version 2.1.8 */
  {
    opacity: 0;
    transform: translateY(30px);
  }

  .over {
    transition: box-shadow 0.3s ease-in-out;
  }

  .over-board {
    transition: box-shadow 0.3s ease-in-out;
  }

  .headline {
    text-transform: initial;
  }

  .icon-container {
    position: absolute;
    margin-right: 0;
    left: 0;
    right: 0;

    .v-btn {
      margin: 0;
    }
  }

  /deep/ .v-card__text {
    padding: 0;
    height: calc(100%);

    iframe {
      background-color: #fff;
      width: 100%;
      height: 100%;
    }

    .open-widget-icon {
      font-size: 64px !important;
    }
  }

  /deep/ .v-card {
    a {
      text-decoration: none;
    }

    box-shadow: 0 3px 1px -2px rgba(0, 0, 0, 0.2), 0 2px 2px 0 rgba(0, 0, 0, 0.14),
    0 1px 5px 0 rgba(0, 0, 0, 0.12);

    &:hover {
      transition: background-color 0.5s ease-in;
      background-color: var(--v-secondary-lighten4);
      cursor: pointer;
    }

    position: relative;

    .v-card__title {
      position: absolute;
      left: 0;
      right: 0;
      bottom: 0;
    }
  }

  /deep/ .v-card__title {
    span,
    small {
      white-space: nowrap;
      letter-spacing: -0.05em;
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
</style>
<style scoped lang="scss">
  .theme--dark {
    .over {
      box-shadow: 0px 0px 4px 2px rgba(255, 255, 255, 0.45) !important;
    }

    /deep/ .v-card__title {
      background-color: var(--v-secondary-lighten2);
    }
  }

  .theme--light {
    .over {
      box-shadow: 0px 0px 5px 3px rgba(0, 0, 0, 0.33) !important;
    }

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
