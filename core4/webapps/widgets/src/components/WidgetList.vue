<template>
  <v-layout>
    <v-navigation-drawer
      v-model="open"
      width="360"
      mini-variant-width="60"
      :mini-variant="miniVariant"
      fixed
      floating
      right
      stateless
      :value="true"
      hide-overlay
    >
      <v-layout class="widget-list">
        <v-flex
          class="px-2"
          v-if="!miniVariant"
        >
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
            label="Search"
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
              <!--    <template v-if="typeof data.item !== 'object'">
                   <v-list-tile-content v-text="data.item"></v-list-tile-content>
                 </template>
                 <template v-else> -->
              <v-list-tile-content>
                <v-list-tile-title v-html="data.item.text"></v-list-tile-title>
              </v-list-tile-content>
              <!-- </template> -->
            </template>
          </v-autocomplete>
        </v-flex>

        <v-toolbar-side-icon
          :large="miniVariant"
          @click="toggleWidgetListOpen()"
        >
          <v-icon color="primary">widgets</v-icon>
        </v-toolbar-side-icon>

      </v-layout>

      <v-slide-y-transition
        v-if="!miniVariant"
        class="pl-2 pr-3 pt-0"
        group
        tag="v-list"
      >
        <!--         <v-layout key="-1000000" row wrap class="pb-2 pt-1">
          <v-chip small @click="tags = [item.label];" style="margin: 2px;"
            v-for="item in autocompleteItems.most"
            :key="item.label"
          >
            <v-avatar class="primary">{{item.count}}</v-avatar>
            {{item.label}}
          </v-chip>
        </v-layout> -->
        <v-subheader key="-99999">
          Widgets
          <v-spacer></v-spacer>
          <v-chip
            small
            color="grey darken-1"
          >
            {{widgets.length}}
          </v-chip>
          <v-btn
            icon
            class="mr-0"
            @click="helpDialogOpen = true"
          >
            <v-icon color="grey">help</v-icon>
          </v-btn>
          <v-dialog
            v-model="helpDialogOpen"
            max-width="960px"
          >
            <v-card>
              <v-card-text>
                <img alt="Howto Drag" src="../assets/howto-drag.jpg" style="width: 100%; height: auto;" class="mb-2">
                Add new Widgets to the current board.
                You can drag and drop widgets into the current board or alternatively use the
                <v-icon>add</v-icon>
                button.
              </v-card-text>
              <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn
                  color="primary"

                  @click="helpDialogOpen=false"
                >Close
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-dialog>
        </v-subheader>
        <drag
          class="drag"
          :class="{'is-not-draggable': item.effectAllowed[0] === 'none'}"
          v-for="item in widgets"
          :key="item.rsc_id"
          :effect-allowed="item.effectAllowed"
          drop-effect="copy"
          :transfer-data="{ widgetId: item.rsc_id }"
        >
          <div @mouseover="onMouseOver(item)" @mouseleave="onMouseLeave(item)">
            <!-- v-list-tile doenst react on mouseover-->
            <v-list-tile
              class="mini-widget"
              avatar
            >
              <!--         <v-list-tile-avatar>
                <v-icon color="grey" medium>{{ item.icon }}</v-icon>
              </v-list-tile-avatar> -->
              <!--            <v-list-tile-avatar>
                            <v-icon v-if="item.effectAllowed[0] === 'copy'" class="widget-drag-icon grey&#45;&#45;text" small>drag_indicator</v-icon>
                          </v-list-tile-avatar>-->
              <v-list-tile-action class="with-hover right">
                <v-tooltip left>
                  <v-icon @click="openInNew(item)"
                          slot="activator"
                          class="grey--text"
                          small
                  >open_in_new
                  </v-icon>
                  <span>Open widget in new tab</span>
                </v-tooltip>
                <v-tooltip left>
                  <v-icon @click="$router.push({ name: 'enter', params: { widgetId: item.rsc_id } })"
                          slot="activator"
                          class="grey--text"
                          small
                  >open_in_browser
                  </v-icon>
                  <span>Open widget</span>
                </v-tooltip>
                <v-tooltip left>
                  <v-icon
                    @click="$router.push({ name: 'help', params: { widgetId: item.rsc_id } })"
                    slot="activator"
                    class="grey--text"
                    small
                  >help
                  </v-icon>
                  <span>Open widget help</span>
                </v-tooltip>
              </v-list-tile-action>

              <v-list-tile-content>
                <v-list-tile-title style="font-weight: 700;">{{ item.title }}</v-list-tile-title>
                <v-tooltip
                  top
                >
                  <template v-slot:activator="{ on }">
                    <v-list-tile-sub-title v-on="on" v-text="item.$qual_name"></v-list-tile-sub-title>
                  </template>
                  <span>{{item.qual_name}}</span>
                </v-tooltip>
              </v-list-tile-content>
              <!--<v-tooltip
                left
                v-if="item.effectAllowed[0] !== 'none'"
              >
                <template v-slot:activator="{ on }">
                  <v-list-tile-action
                    @click="addToBoard(item.rsc_id)"
                    v-on="on"
                    class="with-hover"
                  >
                    <v-icon >add</v-icon>

                  </v-list-tile-action>
                </template>
                <span>Add to board</span>
              </v-tooltip>
              <v-tooltip
                left
                v-else
              >
                <template v-slot:activator="{ on }">
                  <v-list-tile-action
                    @click="removeFromBoard(item.rsc_id)"
                    v-on="on"
                    class="with-hover"
                  >
                    <v-icon >remove</v-icon>

                  </v-list-tile-action>
                </template>
                <span>Remove from board</span>
              </v-tooltip>-->

              <v-list-tile-action class="with-hover">
                <v-tooltip
                  left
                  v-if="item.effectAllowed[0] !== 'none'"
                >
                  <template v-slot:activator="{ on }">
                    <v-icon class="grey--text" v-on="on" @click="addToBoard(item.rsc_id)">
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
                    <v-icon class="grey--text" @click="removeFromBoard(item.rsc_id)" v-on="on">
                      remove_circle_outline
                    </v-icon>
                  </template>
                  <span>Remove to board</span>
                </v-tooltip>
              </v-list-tile-action>
            </v-list-tile>
          </div>
        </drag>

      </v-slide-y-transition>
    </v-navigation-drawer>
  </v-layout>
</template>

<script>
import { mapActions, mapGetters } from 'vuex'
import _ from 'lodash'

export default {
  name: 'widget-list',
  components: {},
  computed: {
    ...mapGetters(['widgetSet', 'widgetListOpen']),
    miniVariant () {
      return !this.widgetListOpen
    },
    widgets () {
      const activeBoard = this.$store.getters.activeBoard
      const activeBoardWidgets = ((activeBoard || {}).widgets) || []
      return this.$store.getters.widgetSet.filter(val => {
        const searchString = val.$search.join(' ')
        if (this.searchInput && this.searchInput.length > 2) {
          return searchString.toLowerCase().includes(this.searchInput)
        }
        if (this.tags != null && this.tags.length) {
          let ret = false
          for (let index = 0; index < this.tags.length; index++) {
            const tag = this.tags[index]
            // if()
            if (searchString.toLowerCase().includes(tag.toLowerCase())) {
              ret = true
              break
            }
          }
          return ret
          // return this.internalTags.includes(val.title.toLowerCase()) || this.internalTags.includes(val.account.toLowerCase())
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
    onMouseOver (item) {
      if (item.effectAllowed[0] === 'none') {
        // this.$bus.$emit('mouseOver', item.rsc_id)
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
    },
    ...mapActions(['addToBoard', 'removeFromBoard', 'toggleWidgetListOpen', 'setWidgetOver']),
    removeTagFromSearch (item) {
      const index = this.tags.indexOf(item.text)
      if (index >= 0) {
        this.tags.splice(index, 1)
      }
    }
  },
  data () {
    return {
      open: true,
      searchInput: '',
      helpDialogOpen: false,
      // miniVariant: false,
      tags: []
    }
  }
}
</script>

<style scoped lang="css">
  div >>> .with-hover {
    height: 56px !important;
  }

  div >>> .with-hover.right {
    padding-top: 0;
  }

  div >>> .with-hover.right .v-icon {
    margin-right: 6px !important;
    margin-bottom: 1px !important;
    margin-top: 0 !important;
    font-size: 14px !important;
  }

  div >>> .with-hover.right .v-tooltip {
    height: 16px !important;
  }

  div >>> .v-chip__content {
    cursor: pointer !important;
  }

  div >>> .v-list__tile {
    padding-left: 0;
    padding-right: 0;
  }

  /*  div >>> .v-list__tile__avatar {
      min-width: 22px;
      width: 22px;
    }*/

  /*  div >>> .v-list__tile__avatar .v-avatar {
    }

    div >>> .v-list__tile__avatar .widget-drag-icon {
      margin-left: -12px;
      padding-top: 3px;
      align-items: flex-start
    }*/

  div >>> .v-list__tile__content {
    padding-left: 6px;
    padding-right: 3px;
  }

  div >>> .v-list__tile__action {
    padding-right: 4px;
    min-width: 32px;
    cursor: grab !important;
  }

  div >>> .v-list__tile__action.with-hover {
    transition: background-color 0.25s ease-in;
  }

  div >>> .v-list__tile__action.with-hover:hover {
    cursor: grab;
  }

  /*  div >>> .v-list__tile__action .v-icon {
      margin-right: 6px;
    }*/

  div >>> .v-subheader {
    font-weight: 600;
    padding-left: 12px;
    padding-right: 3px;
  }
</style>

<style scoped lang="scss">

  .drag {
    cursor: grab;

    &.is-not-draggable {
      cursor: unset !important;
    }
  }

  .widget-list {
    padding-top: 65px;
  }

  .mini-widget {
    min-height: 58px;
    margin-bottom: 6px;
    position: relative;

    &:after {
      content: "";
      position: absolute;
      top: 0;
      right: 0;
      width: 0;
      height: 0;
      border-style: solid;
      border-width: 0 12px 12px 0;
      border-color: transparent darken(#202020, 1) transparent transparent;
      z-index: 100;
    }
  }

  .v-autocomplete {
    position: relative;

    &:after {
      content: "";
      position: absolute;
      top: 0;
      right: 0;
      width: 0;
      height: 0;
      border-style: solid;
      border-width: 0 12px 12px 0;
      z-index: 100;
    }
  }

  .theme--dark {
    /deep/ .v-list__tile__action.with-hover {
      background-color: var(--v-secondary-lighten3);
    }

    /deep/ .v-list__tile__action.with-hover:hover {
      background-color: var(--v-secondary-lighten4);
    }

    .mini-widget {
      background-color: var(--v-secondary-lighten2);

      &:after {
        border-color: transparent darken(#202020, 1) transparent transparent;
      }
    }

    &.v-navigation-drawer {
      background-color: darken(#202020, 1);
    }

    &.v-autocomplete {
      /deep/ .v-input__slot {
        background-color: var(--v-secondary-lighten2) !important;
      }

      &:after {
        border-color: transparent darken(#202020, 1) transparent transparent;
      }
    }
  }

  .theme--light {
    /deep/ .v-chip__content {
      color: #fff;
    }

    /deep/ .v-list__tile__action.with-hover {
      background-color: rgba(0, 0, 0, 0.15);
    }

    /deep/ .v-list__tile__action.with-hover:hover {
      background-color: rgba(0, 0, 0, 0.1);
    }

    .mini-widget {
      background-color: darken(#fff, 5);

      &:after {
        border-color: transparent #fff transparent transparent;
      }
    }

    &.v-autocomplete {
      &:after {
        border-color: transparent #fff transparent transparent;
      }
    }

    .v-navigation-drawer--right {
      box-shadow: 0 2px 4px -1px rgba(0, 0, 0, 0.2),
      0 4px 5px 0 rgba(0, 0, 0, 0.14), 0 1px 10px 0 rgba(0, 0, 0, 0.12) !important;
    }

    .navigation-drawer--mini-variant {
      box-shadow: 0 2px 1px -1px rgba(0, 0, 0, 0.2),
      0 1px 1px 0 rgba(0, 0, 0, 0.14), 0 1px 3px 0 rgba(0, 0, 0, 0.12) !important;
    }
  }
</style>
<style lang="scss">
  .theme--dark {
    /deep/ .dnd-grid-box.placeholder {
      border: 1px dashed #fff !important;
    }

    /deep/ .dnd-grid-box.dragging {
      opacity: 0.5 !important;
    }
  }
</style>
