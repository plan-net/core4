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
    <v-dialog v-model="helpDialog" max-width="960px">
      <v-card>
        <v-card-text>
          <howto type="layer">
            <v-btn slot="button-slot" color="primary" @click.stop="helpDialog=false">Close</v-btn>
          </howto>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-slide-y-transition
    group
      dense class="boards"
      tag="v-list"
    >

    <!-- //LIST OF BOARDS -->
    <template>
      <v-layout row align-center key="-1000">
        <v-flex xs8>
          <v-subheader>
            Board Management
          </v-subheader>
        </v-flex>
        <v-flex class="text-xs-right pr-3">
            <v-btn icon color="grey--text" @click="helpDialog = true">
              <v-icon small >help</v-icon>
            </v-btn>
        </v-flex>
      </v-layout>

      <v-list-tile class="add" @click="nameDialog = true" key="-1001">
        <v-list-tile-action class="board-icon">
          <v-icon color="primary">add_circle</v-icon>
        </v-list-tile-action>
        <v-list-tile-content>
          <v-list-tile-title class="primary--text">
            New board
          </v-list-tile-title>
        </v-list-tile-content>
      </v-list-tile>
      <v-divider key="-1002" class="mt-2 mb-2"></v-divider>
      <template v-if="boards.length">

      <v-list-tile v-for="(item, i) in boards" :key="i" @click="onClick(item, i)" >
        <v-list-tile-action class="board-icon">
          <v-icon>widgets</v-icon>
        </v-list-tile-action>
        <v-list-tile-content>
          <v-list-tile-title>
            {{ item.name }}
          </v-list-tile-title>
        </v-list-tile-content>
          <v-btn @click.stop="onBeforeDelete(item)" flat icon color="grey darken-1">
            <v-icon small>delete</v-icon>
          </v-btn>
      </v-list-tile>
      </template>
    </template>

  </v-slide-y-transition>
  </div>
</template>
<script>
import CreateDialog from '@/components/CreateDialog'
import Howto from '@/components/Howto'
import {
  mapActions
} from 'vuex'

export default {
  components: {
    CreateDialog,
    Howto
  },
  mounted () {
    this.$bus.$on('edit-board-name', this.onEditBoardName)
  },
  methods: {
    ...mapActions(['deleteBoard']),
    onEditBoardName () {
      console.log('onEditBoardName')
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
      helpDialog: false,
      deleteDialog: false,
      itemToDelete: false
    }
  }
}
</script>
<style scoped lang="css">
  div >>> .v-list__tile .v-list__tile__content {
    font-weight: 600;
  }

  .add {
    font-weight: 400;
  }

  .active {
    cursor: default;
    color: #d70f14;
  }

  .active .v-list__tile__title {
    font-weight: 600;
  }

  .active .v-icon {
    color: inherit;
  }
</style>
