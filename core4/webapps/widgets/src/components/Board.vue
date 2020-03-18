<template>
  <!-- https://github.com/kutlugsahin/smooth-dnd -->
  <div v-resize.quiet="onResize">

    <template v-if=noBoards>
      <div class="text-xs-center pt-5">
        <v-tooltip>
          <template v-slot:activator="{ on }">
            <v-btn
              @click="$bus.$emit('edit-board-name')"
              color="primary"
              large
              dark
              fab
              v-on="on"
              fixed
            >
              <v-icon>add</v-icon>
            </v-btn>
          </template>
          <span>Create a board</span>
        </v-tooltip>
      </div>
    </template>

    <template v-else>
      <v-row class="px-5">
        <v-btn
          icon
          @click="prevBoard"
          class="mt-2"
          v-if="boardsCount > 1"
        >
          <v-icon
            large
            class="grey--text"
          >navigate_before</v-icon>
        </v-btn>
        <h1 class="headline mb-4 pt-2">{{name}}
          <v-tooltip top>
            <template v-slot:activator="{ on }">
              <v-btn
                v-on="on"
                @click="$bus.$emit('edit-board-name')"
                icon
                class="mt-0 pt-0"
              >
                <v-icon color="grey--text">edit</v-icon>
              </v-btn>
            </template>
            <span>Change board name</span>
          </v-tooltip>
        </h1>
        <v-btn
          icon
          @click="nextBoard"
          class="mt-2"
          v-if="boardsCount > 1"
        >
          <v-icon
            large
            class="grey--text "
          >navigate_next</v-icon>
        </v-btn>
      </v-row>
    </template>

    <drop
      class="drop pl-4 pr-1"
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
                <template v-slot:activator="{ on }">
                  <v-btn
                    v-on="on"
                    @click="openInNew(widget)"
                    icon
                    small
                    ripple
                  >
                    <v-icon small>open_in_new
                    </v-icon>
                  </v-btn>
                </template>
                <span>Open widget in new tab</span>
              </v-tooltip>
              <v-tooltip top>
                <template v-slot:activator="{ on }">
                  <v-btn
                    v-on="on"
                    @click="$router.push({ name: 'help', params: { widgetId: widget.rsc_id } })"
                    icon
                    small
                    ripple
                  >
                    <v-icon small>help
                    </v-icon>
                  </v-btn>
                </template>
                <span>Open widget help page</span>
              </v-tooltip>
              <v-spacer></v-spacer>
              <v-tooltip top>
                <template v-slot:activator="{ on }">
                  <v-btn
                    v-on="on"
                    @click="removeFromBoard(widget.rsc_id || widget.id)"
                    icon
                    small
                    ripple
                  >
                    <v-icon
                      ripple
                      small
                    >clear
                    </v-icon>
                  </v-btn>
                </template>
                <span>Remove widget from board</span>
              </v-tooltip>
            </v-layout>
            <a v-if="widget.endpoint">
              <v-card-text
                @click="open(widget)"
                :alt="widget.endpoint.enter_url"
              >
                <iframe
                  :src="`${widget.endpoint.card_url}&dark=${dark}`"
                  frameborder="0"
                ></iframe>
              </v-card-text>
            </a>
            <v-card-title>
              <v-icon class="widget-drag-icon">drag_indicator</v-icon>
            </v-card-title>
          </v-card>
        </dnd-grid-box>
      </dnd-grid-container>
    </drop>
  </div>
</template>
<script>
import { mapActions, mapGetters } from 'vuex'
import { Box, Container } from '@dattn/dnd-grid'
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
    open (widget) {
      if (widget.target === 'blank') {
        window.open(widget.enter_url || widget.endpoint.enter_url, '_blank')
      } else {
        this.$router.push({ name: 'enter', params: { widgetId: widget.rsc_id } })
      }
    },
    openInNew (widget) {
      let path = null
      if (widget.target === 'blank') {
        path = widget.enter_url || widget.endpoint.enter_url
      } else {
        path = window.location.pathname + '#/enter/' + widget.rsc_id
      }
      window.open(path, '_blank')
    },
    onResize: lodash.debounce(function () {
      this.elWidth = (this.$el || document.querySelector('body')).offsetWidth
    },
    600),
    ...mapActions(['addToBoard', 'removeFromBoard', 'prevBoard', 'nextBoard']),
    onOver () {
      this.over = true
    },
    onDrop (item) {
      this.addToBoard(item.widgetId)
    }
  },
  data () {
    return {
      elWidth: (this.$el || document.querySelector('body')).offsetWidth,
      isMouseDown: false,
      over: false,
      cellSize: {
        w: 360,
        h: 230
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
    ...mapGetters(['activeBoard', 'dark', 'boardsCount']),
    name () {
      return (this.activeBoard || {}).name
    },
    internalWidgets: {
      // getter
      get: function () {
        if (this.activeBoard && this.activeBoard.widgets) {
          console.log(this.elWidth, this.cellSize.w)
          const offset = Math.floor((this.elWidth - 75) / this.cellSize.w)
          return this.activeBoard.widgets.map((id, index) => {
            const w = this.$store.getters.widgetById(id)
            // const cardUrl = `${w.endpoint.card_url}&theme=${}`
            return Object.assign({},
              w, {
                id,
                position: {
                  x: index % offset,
                  y: Math.floor(index / offset),
                  w: 1,
                  h: 1
                }
              })
          })
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
.list-enter-active,
.list-leave-active {
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
  &:before {
    cursor: pointer;
    content: "";
    display: block;
    position: absolute;
    left: 0;
    right: 0;
    bottom: 38px;
    top: 28px;
    background-color: rgba(0, 0, 255, 0);
    z-index: 1000;
  }

  iframe {
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
}

/deep/ .v-card__title {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  cursor: move;
  height: 38px;
}

.icon-container {
  background-color: rgba(0, 0, 0, 0.175);
}

.icon-container .v-icon,
.widget-drag-icon {
  color: grey !important;
}

.widget-drag-icon {
  cursor: move;
  position: absolute;
  right: 5px;
  top: 6px;
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
    background-color: rgba(0, 0, 0, 0.1);
  }
}

.theme--light {
  .over {
    box-shadow: 0px 0px 5px 3px rgba(0, 0, 0, 0.33) !important;
  }

  /deep/ .v-card__title {
    background-color: rgba(0, 0, 0, 0.1);
  }

  .widget-drag-icon {
    opacity: 1;
  }
}
</style>
