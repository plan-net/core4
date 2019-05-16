<template>
  <v-layout>
    <v-navigation-drawer
      v-model="open"
      :width="scale"
      mini-variant-width="60"
      :mini-variant="miniVariant"
      fixed
      floating
      right
      stateless
      hide-overlay
      class="widget-manager"
    >
      <!-- <div class="wdt-sizes-menu-container" @click="setWidgetSidebarScale(1, true)">-->
      <!--</div>-->
      <v-layout row>

        <!--        <div style="margin: 0 auto; position: relative; left: 20px;">-->

        <v-tabs v-show="!miniVariant"
                v-model="tabs"

                color="transparent"
                slider-color="primary"
        >
          <v-tab>
            Widgets
            <v-btn
              icon small
              class="mx-0"
              @click="helpDialogOpen = true"
            >
              <v-icon small color="grey">help</v-icon>
              <v-dialog
                v-model="helpDialogOpen"
                max-width="960px"
              >
                <v-card>
                  <v-card-text>
                    <img alt="Howto Drag" src="../assets/howto-drag.jpg" style="width: 100%; height: auto;"
                         class="mb-2">
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
          <v-tab

          >
            Boards
            <v-btn
              icon small
              class="mx-0"
              @click="boardHelpDialogOpen = true"
            >
              <v-icon small color="grey">help</v-icon>
            </v-btn>
          </v-tab>
        </v-tabs>
        <v-layout align-center justify-end :class="{row: !miniVariant, 'column reverse': miniVariant}"
                  class="size-toggler pr-3">
          <v-btn @click="setWidgetSidebarScale(3)" small icon class="scaler-container"
                 :disabled="this.scale===this.scales[3]">
            <div class="scaler dreiviertel"></div>
          </v-btn>
          <v-btn @click="setWidgetSidebarScale(2)" small icon class="scaler-container"
                 :disabled="this.scale===this.scales[2]">
            <div class="scaler halb"></div>
          </v-btn>
          <v-btn @click="setWidgetSidebarScale(1)" icon small class="scaler-container"
                 :disabled="this.scale===this.scales[1]">
            <div class="scaler viertel"></div>
          </v-btn>
          <v-btn @click="setWidgetSidebarScale(0)" small icon class="scaler-container"
                 :disabled="this.scale===this.scales[0]">
            <div class="scaler leer"></div>
          </v-btn>
        </v-layout>

        <!--</div>-->
        <!--<v-menu left content-class="wdt-sizes-menu"
                close-on-click
                open-on-hover
                offset-x
                close-on-content-click
        >
          <template v-slot:activator="{ on }">
            <v-btn
              dark @click="setWidgetSidebarScale(1, true)"
              class="wdt-sizes-menu-activator"
              icon
              v-on="on"
            >
              <v-icon color="primary">widgets</v-icon>
            </v-btn>
          </template>
          <v-card>
            <v-card-text style="padding:0;">
              <v-layout row>
                <v-btn @click="setWidgetSidebarScale(3)" small icon class="scaler-container"
                       :disabled="this.scale===this.scales[3]">
                  <div class="scaler dreiviertel"></div>
                </v-btn>
                <v-btn @click="setWidgetSidebarScale(2)" small icon class="scaler-container"
                       :disabled="this.scale===this.scales[2]">
                  <div class="scaler halb"></div>
                </v-btn>
                <v-btn @click="setWidgetSidebarScale(1)" icon small class="scaler-container"
                       :disabled="this.scale===this.scales[1]">
                  <div class="scaler viertel"></div>
                </v-btn>
                <v-btn @click="setWidgetSidebarScale(0)" small icon class="scaler-container"
                       :disabled="this.scale===this.scales[0]">
                  <div class="scaler leer"></div>
                </v-btn>
              </v-layout>
            </v-card-text>
          </v-card>
        </v-menu>-->
      </v-layout>
      <v-tabs-items v-model="tabs" v-show="!miniVariant">
        <v-tab-item
        >
          <widgets-list/>
        </v-tab-item>
        <v-tab-item
        >
          <side-navigation :help-dialog-open="boardHelpDialogOpen" @close="boardHelpDialogOpen = false"/>
        </v-tab-item>
      </v-tabs-items>

    </v-navigation-drawer>
  </v-layout>
</template>

<script>
import { mapActions, mapGetters } from 'vuex'

import WidgetsList from '@/components/WidgetsList'
import SideNavigation from '@/components/SideNavigation'

export default {
  name: 'widget-manager',
  components: {
    WidgetsList,
    SideNavigation
  },
  mounted () {
    this.scale = this.scales[1]
  },
  computed: {
    ...mapGetters(['widgetListOpen', 'dark', 'scales']),
    miniVariant () {
      return this.scale === this.scales[0]
      // return !this.widgetListOpen
    }
  },
  methods: {
    ...mapActions(['toggleWidgetListOpen']),
    setWidgetSidebarScale (index, reset) {
      if (reset) {
        this.scale = (this.scale >= this.scales[1]) ? this.scales[0] : this.scales[1]
      } else {
        this.scale = this.scales[index]
      }
      this.toggleWidgetListOpen(this.scale)
    }
  },
  data () {
    return {

      scale: 0,
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
      content: '';
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
    padding-top: 65px;
  }

  /deep/ .v-autocomplete {
    position: relative;
    margin: 6px 18px 6px 8px !important;

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

  /deep/ .v-toolbar__content {
    padding-right: 6px;
    padding-left: 0;
  }

  .theme--dark {
    div.scaler {
      border-color: #fff;

      &:after {
        background-color: #fff;
      }
    }

    &.v-navigation-drawer, &.widget-list {
      background-color: darken(#202020, 1);
    }

    /deep/ &.v-autocomplete {
      /deep/ .v-input__slot {
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

    /deep/ &.v-autocomplete {
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

  div >>> .v-subheader {
    font-weight: 600;
    padding-left: 12px;
    padding-right: 3px;
  }
</style>

<style scoped lang="scss">
  /deep/ .v-list__tile__title {
    font-weight: 700;
  }

  /deep/ .mini-widget {
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

  .theme--dark {
    /deep/ .v-list__tile__action.with-hover {
      background-color: var(--v-secondary-lighten3);
    }

    /deep/ .v-list__tile__action.with-hover:hover {
      background-color: var(--v-secondary-lighten4);
    }

    /deep/ .mini-widget {
      background-color: var(--v-secondary-lighten2);

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

    /deep/ .mini-widget {
      background-color: darken(#fff, 5);

      &:after {
        border-color: transparent #fff transparent transparent;
      }
    }

  }
</style>
