<template>
  <v-container
    id="board"
    fluid
    class="pa-0"
  >
    <v-row
      no-gutters
      align="center"
    >
      <h1 class="text-h2 mb-4 ml-3"> {{board}}</h1>
      <v-spacer></v-spacer>
      <v-btn
        color="primary"
        class="mr-9"
      >
        <v-icon left>mdi-sticker-plus-outline</v-icon>Add Widget
      </v-btn>
    </v-row>
    <!--   <c4-datatable-plus :config="config"></c4-datatable-plus> -->

    <Muuri></Muuri>

  </v-container>
  <!--   <div class="home" style="border: 1px solid green;">
  </div> -->
</template>

<script>

import { mapState, mapActions } from 'vuex'
import Muuri from '@/components/Muuri.vue'
import store from '@/store'
export default {
  async beforeRouteEnter (to, from, next) {
    await store.dispatch('widgets/initApp')
    next(vm => {})
  },
  async mounted () {
    /*     let board
    if (this.$route.params.board == null) {
      board = this.board
    } else {
      board = this.$route.params.board
    }
    await this.$nextTick()
    this.setActiveBoard(board) */
  },
  methods: {
    ...mapActions('widgets', {
      setActiveBoard: 'setActiveBoard'
    })
  },
  name: 'Home',
  computed: {
    ...mapState('widgets', [
      'board'
    ])
  },
  data () {
    return {
    }
  },
  components: {
    Muuri
  }
}
</script>

<style lang="scss" scoped>
.container {
  max-width: 1074px;
  /*   position: relative;
  max-width: 1%;
  margin: 0 -10px;
  box-sizing: content-box; */
}
</style>
