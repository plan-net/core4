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

    <v-slide-y-transition
      class="pl-2 pr-3 pt-0"
      group
      tag="v-list"
    >

      <!-- //LIST OF BOARDS -->
      <template>
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
import { mapActions } from 'vuex'

export default {
  methods: {
    ...mapActions(['deleteBoard']),
    onBeforeDelete (item) {
      this.itemToDelete = item
      this.deleteDialog = true
    },
    onClick (item, i) {
      this.$store.dispatch('setActiveBoard', item.name)
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
