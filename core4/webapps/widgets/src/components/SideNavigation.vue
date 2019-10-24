<template>
  <div>

    <v-dialog
      v-model="deleteDialog"
      persistent
      max-width="290"
    >
      <v-card>
        <v-card-title class="headline">Delete board</v-card-title>
        <v-card-text>Board {{itemToDelete.name}} will be deleted.</v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            @click.native="deleteDialog = false"
          >Cancel</v-btn>
          <v-btn
            color="primary"
            autofocus
            @click.native="deleteBoard(itemToDelete); deleteDialog = false"
          >Delete
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    <v-dialog
      v-model="helpDialogOpen"
      max-width="960px"
    >
      <v-card>
        <v-card-text>
          <howto type="layer">
            <v-btn
              slot="button-slot"
              color="primary"
              @click.stop="$emit('close')"
            >Close</v-btn>
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

        <!--   <v-list-item class="mini-widget add" @click="nameDialog = true" avatar key="-1001">
          <v-list-item-content>
            <v-list-item-title style="font-weight: 400;">
              New board
            </v-list-item-title>
          </v-list-item-content>
          <v-list-item-action class="board-icon with-hover">
            <v-icon>add_circle</v-icon>
          </v-list-item-action>
        </v-list-item> -->
        <!--<v-divider key="-1002" class="mt-2 mb-2"></v-divider>-->
        <template v-if="boards.length">

          <v-list-item
            :disabled="(item.name === activeBoardName)"
            v-for="(item, i) in boards"
            :key="i"
            @click="onClick(item, i)"
            class="mini-widget"
          >

            <v-list-item-content>
              <v-list-item-title :class="{active: (item.name === activeBoardName)}">
                {{ item.name }}
              </v-list-item-title>
            </v-list-item-content>
            <!--            <v-btn @click.stop="onBeforeDelete(item)" flat icon color="grey darken-1">
                          <v-icon small>delete</v-icon>
                        </v-btn>-->

            <v-list-item-action class="with-hover">
              <v-tooltip left>
                <template v-slot:activator="{ on }">
                  <v-icon
                    class="grey--text"
                    v-on="on"
                    :disabled="(item.name === activeBoardName)"
                    @click.stop="onBeforeDelete(item)"
                  >
                    delete
                  </v-icon>
                </template>
                <span>Delete board</span>
              </v-tooltip>
            </v-list-item-action>
          </v-list-item>
        </template>
      </template>

    </v-slide-y-transition>
    <v-row
      align="start"
      justify="end"
      no-gutters
    >
      <v-btn
        @click="$bus.$emit('edit-board-name', true)"
        class="mx-3 mt-1"
        color="secondary lighten-3"
        dark
      >
        <v-icon
          class="mr-2"
          dark
        >add_circle</v-icon>New board
      </v-btn>
    </v-row>
  </div>
</template>
<script>
// import CreateDialog from '@/components/CreateDialog'
import Howto from '@/components/Howto'
import { mapActions } from 'vuex'

export default {
  components: {
    Howto
  },
  mounted () {
    // this.$bus.$on('edit-board-name', this.onEditBoardName)
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
    /*     onEditBoardName () {
      this.activeBoard = this.$store.getters.activeBoard
      this.nameDialog = true
    }, */
    onBeforeDelete (item) {
      this.itemToDelete = item
      this.deleteDialog = true
    },
    onClick (item, i) {
      this.$store.dispatch('setActiveBoard', item.name)
    }
  },
  /*   watch: {
    nameDialog (val) {
      if (val === false) {
        this.activeBoard = null
      }
    }
  }, */
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
.active .v-icon {
  color: inherit;
}
</style>
