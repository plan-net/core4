<template>
  <div>
    <!-- //CRUD -->
    <create-dialog v-model="nameDialog" :board="activeBoard"></create-dialog>

    <v-dialog v-model="deleteDialog" persistent max-width="290">
      <v-card>
        <v-card-title class="headline">Delete board</v-card-title>
        <v-card-text>Board {{itemToDelete.name}} will be deleted.</v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" @click.native="deleteDialog = false">Cancel</v-btn>
          <v-btn color="primary" autofocus @click.native="deleteBoard(itemToDelete); deleteDialog = false">Delete
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    <v-dialog v-model="helpDialogOpen" max-width="960px">
      <v-card>
        <v-card-text>
          <howto type="layer">
            <v-btn slot="button-slot" color="primary" @click.stop="$emit('close')">Close</v-btn>
          </howto>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-slide-y-transition
      class="pl-2 pr-3 pt-0"
      group
      tag="v-list"
    >

      <!-- //LIST OF BOARDS -->
      <template>
        <!--      <v-layout row align-center key="-1000">
                <v-flex xs8>
                  <v-subheader>
                    Board Management
                  </v-subheader>
                </v-flex>
                <v-flex class="text-xs-right pr-3">
                    <v-btn icon color="grey&#45;&#45;text" @click="helpDialogOpen = true">
                      <v-icon small >help</v-icon>
                    </v-btn>
                </v-flex>
              </v-layout>-->

        <v-list-tile class="mini-widget add" @click="nameDialog = true" avatar key="-1001">
          <v-list-tile-content>
            <v-list-tile-title style="font-weight: 400;">
              New board
            </v-list-tile-title>
          </v-list-tile-content>
          <v-list-tile-action class="board-icon with-hover">
            <v-icon>add_circle</v-icon>
          </v-list-tile-action>
        </v-list-tile>
        <!--<v-divider key="-1002" class="mt-2 mb-2"></v-divider>-->
        <template v-if="boards.length">

          <v-list-tile :disabled="(item.name === activeBoardName)" avatar v-for="(item, i) in boards" :key="i"
                       @click="onClick(item, i)" class="mini-widget">

            <v-list-tile-content>
              <v-list-tile-title :class="{active: (item.name === activeBoardName)}">
                {{ item.name }}
              </v-list-tile-title>
            </v-list-tile-content>
            <!--            <v-btn @click.stop="onBeforeDelete(item)" flat icon color="grey darken-1">
                          <v-icon small>delete</v-icon>
                        </v-btn>-->

            <v-list-tile-action class="with-hover">
              <v-tooltip
                left
              >
                <template v-slot:activator="{ on }">
                  <v-icon style="margin-right: 4px;" small class="grey--text" v-on="on"
                          @click.stop="onBeforeDelete(item)">
                    delete
                  </v-icon>
                </template>
                <span>Delete board</span>
              </v-tooltip>
            </v-list-tile-action>
          </v-list-tile>
        </template>
      </template>

    </v-slide-y-transition>
  </div>
</template>
<script>
import CreateDialog from '@/components/CreateDialog'
import Howto from '@/components/Howto'
import { mapActions } from 'vuex'

export default {
  components: {
    CreateDialog,
    Howto
  },
  mounted () {
    this.$bus.$on('edit-board-name', this.onEditBoardName)
  },
  props: {
    helpDialogOpen: {
      type: Boolean,
      default: false,
      required: true
    }
  },
  methods: {
    ...mapActions(['deleteBoard']),
    onEditBoardName () {
      this.activeBoard = this.$store.getters.activeBoard
      this.nameDialog = true
    },
    onBeforeDelete (item) {
      this.itemToDelete = item
      this.deleteDialog = true
    },
    onClick (item, i) {
      this.$store.dispatch('setActiveBoard', item.name)
    }
  },
  watch: {
    nameDialog (val) {
      if (val === false) {
        this.activeBoard = null
      }
    }
  },
  computed: {
    activeBoardName () {
      return this.$store.getters.activeBoard.name
    },
    boards: {
      get: function () {
        return this.$store.getters.boardsSet
      },
      set: function (newValue) {
      }
    }
  },
  data () {
    return {
      activeBoard: null,
      nameDialog: false,
      deleteDialog: false,
      itemToDelete: false
    }
  }
}
</script>
<style scoped lang="scss">
  .active {
    cursor: default;
    color: #d70f14;

    .v-list__tile__title {
      pointer-events: none;
    }
  }

/*  .active .v-list__tile__title {
    font-weight: 600;
  }*/

  .active .v-icon {
    color: inherit;
  }
</style>
