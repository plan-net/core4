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
            menu-props="auto, closeOnContentClick"
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
              <template v-if="typeof data.item !== 'object'">
                <v-list-tile-content v-text="data.item"></v-list-tile-content>
              </template>
              <template v-else>
                <v-list-tile-content>
                  <v-list-tile-title v-html="data.item.text"></v-list-tile-title>
                </v-list-tile-content>
              </template>
            </template>
          </v-autocomplete>
        </v-flex>
        <v-toolbar-side-icon
          :large="miniVariant"
          @click="miniVariant = !miniVariant"
        >
          <v-icon color="primary">widgets</v-icon>
        </v-toolbar-side-icon>
      </v-layout>

      <v-slide-y-transition
        v-if="!miniVariant"
        class="px-2"
        group
        tag="v-list"
      >
        <v-layout key="-1000000" row wrap class="pb-2 pt-1">
          <v-chip small @click="tags = [item.label];" style="margin: 2px;"
            v-for="item in autocompleteItems.most"
            :key="item.label"
          >
            <v-avatar class="primary">{{item.count}}</v-avatar>
            {{item.label}}
          </v-chip>
        </v-layout>
        <drag
          class="drag"
          v-for="item in widgets"
          :key="item.rsc_id"
          :effect-allowed="item.effectAllowed"
          drop-effect="copy"
          :transfer-data="{ widgetId: item.rsc_id }"
        >
          <v-list-tile class="mini-widget">
            <v-list-tile-content>
              <v-list-tile-title style="font-weight: 700;">{{ item.title }}</v-list-tile-title>
              <v-list-tile-sub-title v-text="item.qual_name"></v-list-tile-sub-title>

            </v-list-tile-content>
            <v-list-tile-action>
              <v-tooltip left>
                <v-btn
                  @click="$router.push({ name: 'widget', params: { widgetId: item.rsc_id } })"
                  slot="activator"
                  icon
                  small
                  ripple
                >
                  <v-icon
                    color="grey lighten-1"
                    small
                  >open_in_new</v-icon>
                </v-btn>
                <span>Open widget</span>
              </v-tooltip>
              <v-tooltip left>
                <v-btn
                  @click="$router.push({ name: 'help', params: { widgetId: item.rsc_id } })"
                  icon
                  slot="activator"
                  small
                  ripple
                >
                  <v-icon
                    color="grey lighten-1"
                    small
                  >help</v-icon>
                </v-btn>
                <span>Help</span>
              </v-tooltip>
            </v-list-tile-action>
          </v-list-tile>
        </drag>

      </v-slide-y-transition>
    </v-navigation-drawer>
  </v-layout>
</template>

<script>
import { mapGetters } from 'vuex'
import _ from 'lodash'
export default {
  name: 'widget-list',
  components: {
  },
  computed: {
    ...mapGetters(['widgetSet']),
    widgets () {
      const activeBoard = this.$store.getters.activeBoard
      const activeBoardWidgets = ((activeBoard || {}).widgets) || []
      return this.$store.getters.widgetSet.filter(val => {
        if (this.searchInput && this.searchInput.length > 2) {
          return val.title.toLowerCase().includes(this.searchInput)
        }
        if (this.tags != null && this.tags.length) {
          let ret = false
          for (let index = 0; index < this.tags.length; index++) {
            const tag = this.tags[index]
            // if()
            if (((val.title || '') + val.qual_name).toLowerCase().includes(tag)) {
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
      let ret = this.widgetSet.map(val => {
        const one = (val.title || '').toLowerCase().split(' ')
        const two = (val.qual_name || '').replace('core4.api.v1.request', '').toLowerCase().split('.')
        return one.concat(two).filter(val => val !== '').filter(val => {
          return val !== 'and' && val !== 'core4' && val !== 'for'
        })
      })
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
    removeTagFromSearch (item) {
      const index = this.tags.indexOf(item.text)
      if (index >= 0) { this.tags.splice(index, 1) }
    }
  },
  data () {
    return {
      open: true,
      searchInput: '',
      miniVariant: false,
      tags: []
    }
  }
}
</script>

<style scoped lang="css">
.mini-widget {
  height: 72px;
}
div >>> .v-chip__content{
  cursor: pointer !important;
}
</style>

<style scoped lang="scss">
.widget-list {
  padding-top: 65px;
}
.mini-widget {
  margin-bottom: 2px;
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
