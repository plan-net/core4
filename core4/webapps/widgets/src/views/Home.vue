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
      <widget-search></widget-search>
<!--        <v-btn
        color="primary"
        class="ml-9"
        @click="createUser"
      >
        <v-icon left>mdi-sticker-plus-outline</v-icon>Dummy
      </v-btn> -->
    </v-row>
    <!--   <c4-datatable-plus :config="config"></c4-datatable-plus> -->

    <Muuri></Muuri>

  </v-container>
  <!--   <div class="home" style="border: 1px solid green;">
  </div> -->
</template>

<script>

import { mapState/* , mapActions */ } from 'vuex'
import Muuri from '@/components/Muuri.vue'
import WidgetSearch from '@/components/WidgetSearch.vue'
import store from '@/store'
import api from '@/store/api'
export default {
  async beforeRouteEnter (to, from, next) {
    await store.dispatch('widgets/initApp')
    next(vm => {})
  },
  async mounted () {
  },
  methods: {
    async createUser () {
      // const ret = await api.__createUser()
      const ret = await api.__createStore()
      console.log(ret)
    }
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
    Muuri,
    WidgetSearch
  }
}
</script>

<style lang="scss" scoped>
.container {
  max-width: 1074px;
}
</style>
