<template>
  <v-container fluid>
    <v-row
      column
      no-gutters
    >
      <v-col
        class="mt-16 pt-8"
        cols="12"
      >
        <img
          class="client"
          src="img/targobank-logo.svg"
          alt=""
        >
      </v-col>
      <v-col
        cols="12"
        class="mt-16 px-3"
      >
        <v-divider></v-divider>
      </v-col>
      <v-col
        cols="12"
        class="mt-4"
      >
        <v-list>
          <v-subheader v-ripple @click="boardsVisible = !boardsVisible">
            MY BOARDS <span class="ml-2" v-if="!boardsVisible">({{boards.length}})</span>
            <v-spacer></v-spacer>
            <v-icon
              small
              v-if="boardsVisible"
            >mdi-menu-up</v-icon>
            <v-icon
              small
              v-else
            >mdi-menu-down</v-icon>
          </v-subheader>
          <v-list-item-group v-if="boardsVisible"
            color="primary"
          >
            <v-list-item
              v-for="(board, i) in boards"
              :key="i"
            >
              <!--    <v-list-item-icon>
                <v-icon v-text="item.icon"></v-icon>
              </v-list-item-icon> -->
              <v-list-item-content>
                <v-list-item-title>
                  {{board.name}}
                </v-list-item-title>
              </v-list-item-content>
            </v-list-item>
          </v-list-item-group>
        </v-list>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import { mapGetters } from 'vuex'
export default {
  computed: {
    ...mapGetters('widgets', [
      'boards'
    ])
  },
  data () {
    return {
      boardsVisible: true
    }
  }
}
</script>

<style lang="scss" scoped>
img.client {
  width: 90%;
  height: auto;
  margin: 0 auto;
  display: block;
}
</style>
