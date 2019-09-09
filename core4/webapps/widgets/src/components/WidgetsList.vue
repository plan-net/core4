<template>
  <div>
    <v-autocomplete
      v-model="tags"
      :disabled="false"
      :items="autocompleteItems.all"
      chips
      box
      solo
      flat
      clearable
      deletable-chips
      auto-select-first
      hide-details
      :open-on-clear="false"
      :menu-props="{auto: true, closeOnContentClick:true}"
      label=""
      item-text="text"
      item-value="text"
      :search-input.sync="searchInput"
      multiple
    >
      <template v-slot:selection="data">
        <v-chip
          :selected="data.selected"
          close
          class="chip--select-multi"
          @input="removeTagFromSearch(data.item)"
        >
          {{ data.item.text }}
        </v-chip>

      </template>

      <template v-slot:item="data">
        <v-list-tile-content>
          <v-list-tile-title v-html="data.item.text"></v-list-tile-title>
        </v-list-tile-content>
      </template>

      <template v-slot:prepend-inner>
        <v-icon>search</v-icon>
      </template>
      <template v-slot:append-outer>
        <search-options-menu />

      </template>
    </v-autocomplete>
    <v-slide-y-transition
      class="pl-2 pr-3 pt-0 layout row wrap"
      group
      tag="v-list"
    >
      <v-flex
        :class="widgetClass"
        v-for="item in widgets"
        :key="item.rsc_id"
        @mouseover="onMouseOver(item)"
        @mouseleave="onMouseLeave(item)"
      >
        <drag
          class="drag"
          :class="{'is-not-draggable': item.effectAllowed[0] === 'none'}"
          :effect-allowed="item.effectAllowed"
          drop-effect="copy"
          :transfer-data="{ widgetId: item.rsc_id }"
        >
          <v-list-tile
            class="mini-widget"
            avatar
          >
            <v-list-tile-action class="with-hover right">
              <v-tooltip left>
                <v-icon
                  @click="openInNew(item)"
                  slot="activator"
                  small
                >open_in_new
                </v-icon>
                <span>Open widget in new tab</span>
              </v-tooltip>
              <v-tooltip left>
                <v-icon
                  @click="$router.push({ name: 'enter', params: { widgetId: item.rsc_id } })"
                  slot="activator"
                  small
                >open_in_browser
                </v-icon>
                <span>Open widget</span>
              </v-tooltip>
              <v-tooltip left>
                <v-icon
                  @click="$router.push({ name: 'help', params: { widgetId: item.rsc_id } })"
                  slot="activator"
                  small
                >help
                </v-icon>
                <span>Open widget help</span>
              </v-tooltip>
            </v-list-tile-action>

            <v-list-tile-content>
              <v-list-tile-title>{{ item.title }}</v-list-tile-title>
              <v-tooltip top>
                <template v-slot:activator="{ on }">
                  <v-list-tile-sub-title
                    v-on="on"
                    v-text="item.$qual_name"
                  ></v-list-tile-sub-title>
                </template>
                <span>{{item.qual_name}}</span>
              </v-tooltip>
            </v-list-tile-content>
            <v-list-tile-action class="with-hover">
              <v-tooltip
                left
                v-if="item.effectAllowed[0] !== 'none'"
              >
                <template v-slot:activator="{ on }">
                  <v-icon
                    v-on="on"
                    @click="addToBoard(item.rsc_id)"
                  >
                    add_circle_outline
                  </v-icon>
                </template>
                <span>Add to board</span>
              </v-tooltip>
              <v-tooltip
                left
                v-else
              >
                <template v-slot:activator="{ on }">
                  <v-icon
                    @click="removeFromBoard(item.rsc_id)"
                    v-on="on"
                  >
                    remove_circle_outline
                  </v-icon>
                </template>
                <span>Remove to board</span>
              </v-tooltip>
            </v-list-tile-action>
          </v-list-tile>
        </drag>
      </v-flex>
    </v-slide-y-transition>
  </div>
</template>

<script>
import { mapActions, mapGetters, mapState } from 'vuex'
import SearchOptionsMenu from '@/components/sub/SearchOptionsMenu'
import _ from 'lodash'

export default {
  name: 'widget-list',
  components: {
    SearchOptionsMenu
  },
  data () {
    this.ti = 0
    return {
      widgetClass: 'xs12',
      searchInput: '',
      tags: []
    }
  },
  props: {
    scale: {
      type: Number,
      default: 360,
      required: true
    }
  },
  mounted () {
    this.updateLayout()
  },
  watch: {
    scale () {
      this.updateLayout()
    }
  },
  methods: {
    updateLayout () {
      window.clearTimeout(this.ti)
      this.ti = window.setTimeout(function () {
        const widgetManagerW = document.querySelector('.widget-manager').offsetWidth
        if (this.scale !== this.scales[0]) {
          const widgetManagerW2 = widgetManagerW / 400
          const p2 = Math.ceil(widgetManagerW2)
          const xs = `xs${12 / p2}`
          this.widgetClass = xs
        } else {
          this.widgetClass = 'xs12'
        }
      }.bind(this), 400)
    },
    ...mapActions(['addToBoard', 'removeFromBoard', 'setWidgetOver']),
    removeTagFromSearch (item) {
      const index = this.tags.indexOf(item.text)
      if (index >= 0) {
        this.tags.splice(index, 1)
      }
    },
    openInNew (widget) {
      let path = null
      if (widget.target === 'blank') {
        path = widget.enter_url || widget.endpoint.enter_url
      } else {
        path = '/#/enter/' + widget.rsc_id
      }
      window.open(path, '_blank')
    },
    onMouseOver (item) {
      if (item.effectAllowed[0] === 'none') {
        this.setWidgetOver({
          $over: true,
          id: item.rsc_id
        })
      }
    },
    onMouseLeave (item) {
      if (item.effectAllowed[0] === 'none') {
        this.setWidgetOver({
          $over: false,
          id: item.rsc_id
        })
      }
    }
  },

  computed: {
    ...mapState([
      'scales'
    ]),
    ...mapGetters(['widgetSet']),
    widgets () {
      const activeBoard = this.$store.getters.activeBoard
      const activeBoardWidgets = ((activeBoard || {}).widgets) || []

      return this.widgetSet.filter(val => {
        const searchString = val.$search.join(' ')
        if (this.searchInput && this.searchInput.length > 2) {
          return searchString.toLowerCase().includes(this.searchInput)
        }
        if (this.tags != null && this.tags.length) {
          let ret = false
          for (let index = 0; index < this.tags.length; index++) {
            const tag = this.tags[index]
            if (searchString.toLowerCase().includes(tag.toLowerCase())) {
              ret = true
              break
            }
          }
          return ret
        }
        return true
      }).map(val => {
        const effect = activeBoardWidgets.includes(val.rsc_id) ? 'none' : 'copy'
        val.effectAllowed = [effect]
        return val
      })
    },
    autocompleteItems () {
      // TODO - all words seperated
      let ret = this.widgetSet.map(val => val.$search) // arr of arrs
      ret = [].concat.apply([], ret) // flatten [['s'], 'x'] => ['s', 'x']
      const count = _.countBy(ret)
      const most = _.sortBy(
        Object.keys(count).filter(key => count[key] > 2).map(val => {
          return {
            label: val,
            count: count[val]
          }
        }), o => o.count).reverse()

      ret = [...new Set(ret)]// unique
      ret = ret.map(
        text => {
          return {
            text
          }
        }
      )
      return {
        most,
        all: ret.filter(i => new RegExp(this.tag, 'i').test(i.text))
      }
    }

  }
}
</script>

<style scoped lang="scss">
/deep/ .v-icon {
  color: grey !important;
}

.v-list > .xs6,
.v-list > .xs4 {
  padding-right: 6px;
}

.drag {
  cursor: grab;

  &.is-not-draggable {
    cursor: unset !important;
  }
}

.theme--dark {
  /deep/ .dnd-grid-box.placeholder {
    border: 1px dashed #fff !important;
  }

  /deep/ .dnd-grid-box.dragging {
    opacity: 0.5 !important;
  }
}
</style>
