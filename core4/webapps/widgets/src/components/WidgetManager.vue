<template>
  <v-navigation-drawer
    v-model="open"
    :width="currScaleAbs"
    mini-variant-width="40"
    :mini-variant="miniVariant"
    fixed
    floating
    right
    stateless
    hide-overlay
    class="widget-manager"
  >
    <v-row
      no-gutters
      class=""
    >
      <v-col>
        <v-tabs
          v-show="!miniVariant"
          v-model="tabs"
        >
          <v-tab>
            Widgets
            <v-btn
              icon
              small
              class="mr-0 ml-2"
              @click.stop="boardHelpDialogOpen = true"
            >
              <v-icon
                small
                color="grey"
              >help</v-icon>
              <v-dialog
                v-model="boardHelpDialogOpen"
                max-width="960px"
              >
                <v-card>
                  <v-card-text>
                    <howto type="layer">
                      <v-btn
                        slot="button-slot"
                        color="primary"
                        @click.stop="boardHelpDialogOpen = false"
                      >Close</v-btn>
                    </howto>
                  </v-card-text>
                </v-card>
              </v-dialog>
            </v-btn>
          </v-tab>
          <v-tab>

            <span>Boards</span>
            <v-spacer></v-spacer>
            <v-btn
              icon
              small
              class="mr-0 ml-2"
              @click.stop="helpDialogOpen = true"
            >
              <v-icon
                small
                color="grey"
              >help</v-icon>
              <v-dialog
                v-model="helpDialogOpen"
                max-width="960px"
              >
                <v-card>
                  <v-card-text>
                    <img
                      alt="Howto Drag"
                      src="../assets/howto-drag.jpg"
                      style="width: 100%; height: auto;"
                      class="mb-2"
                    >
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

            </v-btn>

          </v-tab>
        </v-tabs>
      </v-col>
      <v-col>
        <v-row
          no-gutters
          align="center"
          justify="end"
          :class="{'pt-2': !miniVariant}"
          class="size-toggler pr-3"
        >
          <v-btn
            @click="setCurrScale({index: 3, persist: true})"
            small
            icon
            class="scaler-container"
            :disabled="currScalePerc===scales[3]"
          >
            <div class="scaler dreiviertel"></div>
          </v-btn>
          <v-btn
            @click="setCurrScale({index: 2, persist: true})"
            small
            icon
            class="scaler-container"
            :disabled="currScalePerc===scales[2]"
          >
            <div class="scaler halb"></div>
          </v-btn>
          <v-btn
            @click="setCurrScale({index: 1, persist: true})"
            icon
            small
            class="scaler-container"
            :disabled="currScalePerc===scales[1]"
          >
            <div class="scaler viertel"></div>
          </v-btn>
          <v-btn
            @click="setCurrScale({index: 0, persist: true})"
            small
            icon
            class="scaler-container"
            :disabled="currScalePerc===scales[0]"
          >
            <div class="scaler leer"></div>
          </v-btn>
        </v-row>
      </v-col>
    </v-row>

    <v-tabs-items
      v-model="tabs"
      v-show="!miniVariant"
    >
      <v-tab-item>
        <widgets-list :scale="currScalePerc" />
      </v-tab-item>
      <v-tab-item>
        <side-navigation />
      </v-tab-item>
    </v-tabs-items>
  </v-navigation-drawer>
</template>

<script>
import { mapActions, mapGetters } from 'vuex'

import WidgetsList from '@/components/WidgetsList'
import SideNavigation from '@/components/SideNavigation'
import Howto from '@/components/Howto'

export default {
  name: 'widget-manager',
  components: {
    WidgetsList,
    SideNavigation,
    Howto
  },
  mounted () {
  },
  computed: {
    ...mapGetters(['dark', 'scales', 'currScalePerc', 'currScaleAbs']),
    miniVariant () {
      return this.currScalePerc === this.scales[0]
    }
  },
  methods: {
    ...mapActions(['setCurrScale'])
  },
  data () {
    return {
      tabs: null,
      open: true,
      helpDialogOpen: false,
      boardHelpDialogOpen: false
    }
  }
}
</script>

<style scoped lang="scss">
.scaler-container {
  margin: 0;
}

div.scaler {
  width: 16px;
  height: 11px;
  position: relative;
  border: 2px solid;
  &:after {
    position: absolute;
    content: "";
    right: 0;
    top: 0;
    bottom: 0;
  }
}

.v-btn[disabled] {
  .scaler {
    border-color: var(--v-primary-base);

    &:after {
      background-color: var(--v-primary-base);
    }
  }
}
div.leer {
  &:after {
    left: 12px;
  }
}

div.viertel {
  &:after {
    left: 9px;
  }
}

div.halb {
  &:after {
    left: 6px;
  }
}

div.dreiviertel {
  &:after {
    left: 3px;
  }
}

.widget-manager {
  padding-top: 60px;
}

::v-deep .v-autocomplete {
  position: relative;
  margin-left: -12px !important;
  max-width: none !important;
  &.ecke {
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
}

::v-deep .v-toolbar__content {
  padding-right: 6px;
  padding-left: 0;
}

.theme--dark {
  div.scaler {
    border-color: grey;

    &:after {
      background-color: grey;
    }
  }

  &.v-navigation-drawer,
  &.v-tabs-items {
    background-color: darken(#202020, 1);
    background: darken(#202020, 1);
  }
  ::v-deep &.v-tabs-bar {
    background-color: darken(#202020, 1) !important;
    background: darken(#202020, 1);
  }

  ::v-deep &.v-autocomplete {
    ::v-deep .v-input__slot {
      background-color: var(--v-secondary-lighten2) !important;
    }

    &:after {
      border-color: transparent darken(#202020, 1) transparent transparent;
    }
  }
}

.theme--light {
  div.scaler {
    border-color: var(--v-secondary-lighten3);

    &:after {
      background-color: var(--v-secondary-lighten3);
    }
  }

  ::v-deep &.v-autocomplete {
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
<style scoped lang="css">
div >>> .with-hover {
  height: 64px !important;
  width: 32px;
  padding-left: 4px;
  flex: none;
}

div >>> .with-hover.right {
  padding-top: 2px;
}

div >>> .with-hover.right .v-icon {
  margin-right: 4px !important;
  margin-bottom: 2px !important;
  margin-top: 0 !important;
  font-size: 18px !important;
}
div >>> .with-hover.right .v-icon:hover {
  color: var(--v-primary-base) !important;
}

div >>> .with-hover.right .v-tooltip {
  height: 16px !important;
}

div >>> .v-chip__content {
  cursor: pointer !important;
}

div >>> .v-list-item {
  padding-left: 0;
  padding-right: 0;
}

div >>> .v-list-item__content {
  padding-left: 6px;
  padding-right: 3px;
}

div >>> .v-list-item__action {
  cursor: grab !important;
}

div >>> .v-list-item__action.with-hover {
  transition: background-color 0.25s ease-in;
}

div >>> .v-list-item__action.with-hover:hover {
  cursor: grab;
}
</style>

<style scoped lang="scss">
::v-deep .v-list-item__title {
  font-weight: 700;
  margin-bottom: 6px;
}
::v-deep .v-list-item.mini-widget {
  height: 66px;
  min-height: 66px;
  margin-bottom: 6px;
}
// TODO: SearchOptionsMenu.vue
::v-deep .v-input__append-outer {
  margin-top: 0 !important;
  margin-left: 0 !important;
  .append-to-search {
    height: 56px;
  }
}

::v-deep .mini-widget,
::v-deep .append-to-search {
  position: relative;
  &:after {
    content: "";
    position: absolute;
    top: 0;
    right: 0;
    width: 0;
    height: 0px;
    border-style: solid;
    border-width: 0 12px 12px 0;
    border-color: transparent darken(#202020, 1) transparent transparent;
    z-index: 100;
  }
}
::v-deep .mini-widget {
  overflow: hidden;
  &:after {
    top: -54px;
  }
}
.theme--dark {
  ::v-deep .v-list-item__action.with-hover {
    background-color: var(--v-secondary-lighten3);
  }

  ::v-deep .v-list-item__action.with-hover:hover {
    background-color: var(--v-secondary-lighten4);
  }

  ::v-deep .mini-widget,
  ::v-deep .append-to-search {
    background-color: var(--v-secondary-lighten2);

    &:after {
      border-color: transparent darken(#202020, 1) transparent transparent;
    }
  }
}

.theme--light {
  ::v-deep .v-chip__content {
    color: #fff;
  }

  ::v-deep .v-list-item__action.with-hover {
    background-color: rgba(0, 0, 0, 0.15);
  }

  ::v-deep .v-list-item__action.with-hover:hover {
    background-color: rgba(0, 0, 0, 0.1);
  }

  ::v-deep .mini-widget,
  ::v-deep .append-to-search {
    background-color: darken(#fff, 5);

    &:after {
      border-color: transparent #fff transparent transparent;
    }
  }
}
</style>
